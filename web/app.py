import logging; logging.basicConfig(level=logging.INFO)
import asyncio, os, json, time,markdown2
from conf.config import getConfig
from datetime import datetime
import orm
from jinja2 import Environment, FileSystemLoader, Markup

from handlers import redirect

from aiohttp import web

from coreweb import add_routes, add_static,add_upload

async def loggerfactory(app, handler):
	async def logger(request):
		logging.info('Request: %s %s' % (request.method, request.path))
		try:
			response = await handler(request)
		except web.HTTPException as ex:
			logging.info(ex)
			return redirect('/404')
		return response
	return logger

async def response_factory(app, handler):
	async def response(request):
		r = await handler(request)
		logging.info('Response handler... %s' % r)
		if isinstance(r, web.StreamResponse):
			return r
		if isinstance(r, bytes):
			resp = web.Response(body=r)
			resp.content_type = 'application/octet-stream'
			return resp
		if isinstance(r, str):
			if r.startswith('redirect:'):
				return web.HTTPFound(r[9:])
			resp = web.Response(body=r.encode('utf-8'))
			resp.content_type = 'text/html;charset=utf-8'
			return resp
		if isinstance(r, dict):
			r['website_host'] = app['website_host']
			template = r.get('__template__')
			if template is None:
				resp = web.Response(
					body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
				resp.content_type = 'application/json;charset=utf-8'
				return resp
			else:
				resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
				resp.content_type = 'text/html;charset=utf-8'
				return resp
		if isinstance(r, int) and r >= 100 and r < 600:
			return web.Response(r)
		if isinstance(r, tuple) and len(r) == 2:
			t, m = r
			if isinstance(t, int) and t >= 100 and t < 600:
				return web.Response(t, str(m))
		resp = web.Response(body=str(r).encode('utf-8'))
		resp.content_type = 'text/plain;charset=utf-8'
		return resp
	return response

def init_jinja2(app, **kw):
	logging.info('init jinja2...')
	options = dict(
		autoescape = kw.get('autoescape', True),
		block_start_string = kw.get('block_start_string', '{%'),
		block_end_string = kw.get('block_end_string', '%}'),
		variable_start_string = kw.get('variable_start_string', '{{'),
		variable_end_string = kw.get('variable_end_string',	'}}'),
		auto_reload = kw.get('auto_reload', True)
	)
	path = kw.get('path', None)
	if path is None:
		path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
	logging.info('set jinja2 template path: %s' % path)
	env = Environment(loader=FileSystemLoader(path), **options)
	filters = kw.get('filters', None)
	if filters is not None:
		for name, f in filters.items():
			env.filters[name] = f
	app['__templating__'] = env

#markdown的格式化
def custom_markdown(value):
	return markdown2.markdown(value, extras={"fenced-code-blocks", "cuddled-lists", "metadata", "tables", "spoiler"})

def datetime_filter(t):
	logging.info(t)
	delta = int(time.time() - t)
	if delta < 60:
		return Markup("1分钟前").striptags()
	if delta < 3600:
		return Markup('%s分钟前' % (delta // 60)).striptags()
	if delta < 86400:
		return Markup('%s小时前' % (delta // 3600)).striptags()
	if delta < 604800:
		return Markup('%s天前' % (delta // 86400)).striptags()
	dt = datetime.fromtimestamp(t)
	return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


async def init(loop):
	config_data = getConfig()
	db = config_data.get('blog_db')
	website = config_data.get('website')
	if(db is None):
		raise Exception('Please check your config...')
	await orm.create_pool(loop, **db)
	# (self, *, logger = web_logger, loop = None, router = None, handler_factory = RequestHandlerFactory, middlewares = (), debug = False)
	app = web.Application(loop=loop, middlewares = [loggerfactory, response_factory])
	app['website_host'] = website.get('host')
	init_jinja2(app, filters = dict(datetime=datetime_filter))
	add_routes(app, 'handlers')
	add_static(app)
	add_upload(app)
	srv = await loop.create_server(app.make_handler(), website.get('host'), website.get('port'))
	logging.info('Server started at http://%s:%s...' % (website.get('host'), website.get('port')))
	return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
