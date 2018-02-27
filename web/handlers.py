import datetime
import hashlib
import logging
import re,functools
from io import BytesIO

from aiohttp import web

from apiHandler import APIValueError, APIResult,APIUploadResult
from common import emailThread,rand_color,savefile,next_id
from conf.config import config
from coreweb import get,post
from model import User,Category,Blogs,BlogCategory,BlogTag,Tag,Comments,currentTime
from orm import Page,select,execute,DateTimeField
from utils import getWebCookie, user2cookie,setWebCookie,jsonResult,urldecode,class_to_dict
from verify import create_validate_code

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

@get('/')
def index(request):
    try:
        # 获取博客分类和文章分类下的文章
        category_sql = ['%s %s %s' % (
            'select B.id,B.title,count(*) num from blog_category as A',
            'left join category as B on A.category_id = B.id where B.is_delete = 0',
            'group by A.category_id'
        )]
        blog_category = yield from select(category_sql, [])
        # 获取热门文章
        hot_blog_sql = ['select id,title,view_count from blogs order by view_count desc limit 10']
        hot_blog = yield from select(hot_blog_sql, [])
        return display('index', {'blog_category': blog_category, 'hot_blog': hot_blog})
    except Exception as e:
        logging.info(e)
        return redirect('/404')

#文章的分类
@get('/category/{category_id}')
def category(*, request, category_id):
    # 获取当前分类的名字
    category = yield from Category.findOne([category_id])
    if category is not None:
        # 获取博客分类和文章分类下的文章
        category_sql = ['%s %s %s' % (
            'select B.id,B.title,count(*) num from blog_category as A',
            'left join category as B on A.category_id = B.id where B.is_delete = 0',
            'group by A.category_id'
        )]
        blog_category = yield from select(category_sql, [])
        # 获取热门文章
        hot_blog_sql = ['select id,title,view_count from blogs order by view_count desc limit 10']
        hot_blog = yield from select(hot_blog_sql, [])
        return display('category', {'blog_category': blog_category, 'hot_blog': hot_blog, 'category': category})
    else:
        return redirect('/404')

# 标签文章分类
@get('/tag/{tag_id}')
def tag(*, request, tag_id):
# 获取当前标签分类的名字
    tag = yield from Tag.findOne([tag_id])
    if tag is not None:
        # 获取博客分类和文章分类下的文章
        category_sql = ['%s %s %s' % (
            'select B.id,B.title,count(*) num from blog_category as A',
            'left join category as B on A.category_id = B.id where B.is_delete = 0',
            'group by A.category_id'
        )]
        blog_category = yield from select(category_sql, [])
        # 获取热门文章
        hot_blog_sql = ['select id,title,view_count from blogs order by view_count desc limit 10']
        hot_blog = yield from select(hot_blog_sql, [])
        return display('tag', {'blog_category': blog_category, 'hot_blog': hot_blog, 'tag': tag})
    else:
        return redirect('/404')


#文章内容页
@get('/blog/{id}')
def get_blog(*, request, id):
    blog = yield from Blogs.findOne(id)
    if blog is not None:
        # 访问次数加1
        sql = 'update blogs set view_count = view_count + 1 where id = ?'
        yield from execute(sql, [id])
        #获取文章分类
        category_sql = ['%s %s' % (
            'select GROUP_CONCAT(B.id) category_id,GROUP_CONCAT(B.title) category_title from blog_category as A ',
            'left join category as B on A.category_id = B.id')]
        category_sql.append('where')
        category_sql.append('blog_id=?')
        category = yield from select(category_sql, [id])
        #获取文章标签
        tag_sql = ['%s %s' % ('select GROUP_CONCAT(B.id) tag_id,GROUP_CONCAT(B.title) tag_title from blog_tag as A',
                              'left join tag as B on A.tag_id = B.id ')]
        tag_sql.append('where')
        tag_sql.append('blog_id=?')
        tag = yield from select(tag_sql, [id])
        #获取作者
        user = yield from User.findOne(blog['user_id'])
        #获取评论
        comment_sql = ['select *,(select count(*) from comments where parent = A.id) as children from comments as A ']
        comment_sql.append('where')
        comment_sql.append('display = 1 and parent = 0 and blog_id=?')
        comments = yield from select(comment_sql, [id])
        blog['comment_num'] = len(comments)
        if len(comments) > 0:
            for k in range(len(comments)):
                comments[k]['child'] = []
                child_sql = ['select * from comments']
                child_sql.append('where')
                child_sql.append('display = 1 and parent = ?')
                children = yield from select(child_sql, comments[k].get('id'))
                comments[k]['child'] = children
                blog['comment_num'] = blog['comment_num'] + len(children)
            blog['comments'] = comments
        if user is not None:
            blog['author'] = user['name']
        if len(category) > 0:
            if category[0].get('category_id') is not None:
                blog['category_id'] = category[0].get('category_id').split(',')
            if category[0].get('category_title') is not None:
                blog['category_title'] = category[0].get('category_title').split(',')
        if len(tag) > 0:
            if tag[0].get('tag_id') is not None:
                blog['tag_id'] = tag[0].get('tag_id').split(',')
            if tag[0].get('tag_title') is not None:
                blog['tag_title'] = tag[0].get('tag_title').split(',')
        logging.info(blog)
        return display('content' ,{'blog': blog})
    else:
        return redirect('/404')

#文章归档
@get('/archive')
def archive(request):
    blogs = yield from Blogs.findAll(orderBy='create_time desc')
    year = {}
    for row in blogs:
        create_time = datetime.datetime.strptime(row.create_time, '%Y-%m-%d %H:%M:%S')
        month_day = {}
        if year.get(create_time.year) is None:
            month_day['%s月%s日' % (create_time.month,create_time.day)] = []
            month_day['%s月%s日' % (create_time.month,create_time.day)].append(row)
            year[create_time.year] = month_day
        else:
            if year.get(create_time.year).get('%s月%s日' % (create_time.month,create_time.day)) is None:
                year[create_time.year]['%s月%s日' % (create_time.month,create_time.day)] = []
                year[create_time.year]['%s月%s日' % (create_time.month, create_time.day)].append(row)
            else:
                year[create_time.year]['%s月%s日' % (create_time.month, create_time.day)].append(row)
    return display('archive',{'year' : year})

#关于自己
@get('/about')
def about(request):
    file_object = open('../data/about.md', encoding='UTF-8')
    try:
        all_the_text = file_object.read()
    finally:
        file_object.close()
    return display('about', {'content': all_the_text})

#友情链接
@get('/link')
def link(request):
    file_object = open('../data/link.md', encoding='UTF-8')
    try:
        all_the_text = file_object.read()
    finally:
        file_object.close()
    return display('link', {'content': all_the_text})


#标签分类
@get('/tags')
def tags(request):
    # 获取博客分类和文章分类下的文章
    category_sql = ['%s %s %s' % (
        'select B.id,B.title,count(*) num from blog_category as A',
        'left join category as B on A.category_id = B.id where B.is_delete = 0',
        'group by A.category_id'
    )]
    blog_category = yield from select(category_sql, [])
    # 获取热门文章
    hot_blog_sql = ['select id,title,view_count from blogs order by view_count desc limit 10']
    hot_blog = yield from select(hot_blog_sql, [])
    # 获取博客分类和文章分类下的文章
    tag_sql = ['%s %s %s' % (
        'select A.id,A.title,count(blog_id) num from tag as A',
        'left join blog_tag as B on A.id = B.tag_id',
        'group by A.id'
    )]
    tags = yield from select(tag_sql, [])
    for v in tags:
        v['style'] = rand_color()
    return display('tags', {'data': tags, 'blog_category': blog_category, 'hot_blog': hot_blog})

@get('/register')
def register(request):
    return display('register')

@get('/login')
def login(request):
    return display('login')

@get('/verify')
def verify(request):
    validate_code = create_validate_code()
    img = validate_code[0]
    mstream = BytesIO()
    img.save(mstream, format = "GIF")
    config['verify'] = validate_code[1]
    r = web.Response()
    r.content_type = 'image/gif'
    r.body = mstream.getvalue()
    return r

@get('/404')
def error():
    return display('404')


#登录权限验证
def auth(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user_cookie = getWebCookie(kwargs['request'], 'user')
        user_email = getWebCookie(kwargs['request'], 'email')
        # 判断cookie是否存在
        if (user_email is None):
            return redirect('/login')
        else:
            session_user_email = config['_session'].get(user_email)
            if (session_user_email is not None):
                if (user_cookie == session_user_email):
                    return func(*args, **kwargs)
                else:
                    return redirect('/login')
            else:
                return redirect('/login')
    return wrapper

@get('/logout')
@auth
def logout(request):
    user_email = getWebCookie(request, 'email')
    if user_email is not None:
        config['_session'][user_email] = None
    return redirect('/')

######################################后台管理#########################################
#后台管理
@get('/admin')
@auth
def admin(request):
    user_name = getWebCookie(request, 'name')
    return display('admin',{'name':user_name})

#添加文章
@get('/add/article')
@auth
def add_article(request):
    return display('add_article')

#添加新分类
@get('/add/category')
@auth
def add_category(request):
    return display('add_category')

#修改文章
@get('/edit/article/{blog_id}')
@auth
def edit_article(*, request, blog_id):
    blog = yield from Blogs.findOne(blog_id)
    if blog is not None:
        # 获取文章分类
        category_sql = ['%s %s' % (
            'select GROUP_CONCAT(B.id) category_id,GROUP_CONCAT(B.title) category_title from blog_category as A ',
            'left join category as B on A.category_id = B.id')]
        category_sql.append('where')
        category_sql.append('blog_id=?')
        category = yield from select(category_sql, [blog_id])
        # 获取文章标签
        tag_sql = ['%s %s' % ('select GROUP_CONCAT(B.id) tag_id,GROUP_CONCAT(B.title) tag_title from blog_tag as A',
                              'left join tag as B on A.tag_id = B.id ')]
        tag_sql.append('where')
        tag_sql.append('blog_id=?')
        tag = yield from select(tag_sql, [blog_id])

        if len(category) > 0:
            if category[0].get('category_id') is not None:
                blog['category_id'] = category[0].get('category_id').split(',')
            if category[0].get('category_title') is not None:
                blog['category_title'] = category[0].get('category_title').split(',')
        if len(tag) > 0:
            if tag[0].get('tag_id') is not None:
                blog['tag_id'] = tag[0].get('tag_id').split(',')
            if tag[0].get('tag_title') is not None:
                blog['tag_title'] = tag[0].get('tag_title').split(',')
        logging.info(blog)
        #blog['content'] = """%s""" % (blog['content'])
        return display('edit_article', {'blog': blog})
    else:
        return redirect('/404')

# 修改文章
@get('/edit/category/{category_id}')
@auth
def edit_article(*, request, category_id):
    cate = yield from Category.findOne(category_id)
    if cate is not None:
        return display('edit_category', {'cate': cate})
    else:
        return redirect('/404')

# 图片上传
@post('/upload')
@auth
def upload(*, request):
    r = web.Response()
    data = yield from request.post()
    try:
        if data['editormd-image-file'] is not None:
            if hasattr(data['editormd-image-file'], 'file'):
                iofile = data['editormd-image-file'].file
                filename = data['editormd-image-file'].filename
                save_path = yield from savefile(iofile, filename)
                result = APIUploadResult(1, '上传成功！', save_path)
            else:
                result = APIUploadResult(0, '未选择文件！', '')
        else:
            result = APIUploadResult(0, '未选择文件！', '')
    except APIUploadResult:
        result = APIUploadResult(0, '服务器错误，请稍候再上传！', '')
    return jsonResult(r, result)


#################################API接口#################################################
#注册接口
@post('/api/register')
def api_register(*, name, email, passwd):
    r = web.Response()
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = yield from User.findAll('email=?', [email])
    if len(users) > 0:
        result =  APIResult(0, '', 'Email is already in use.')
    else:
        sha1_passwd = '%s:%s' % ('hearain', passwd)
        user = User(name=name.strip(),
                    email=email,
                    password=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
                    logo='http://www.gravatar.com/avatar/%s?d=wavatar&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest()
                    )
        id = yield from user.save()
        #设置session
        config['_session'][user.email] = user2cookie(user, 86400)
        setWebCookie(r, 'user', config['_session'][user.email])
        setWebCookie(r, 'email', user.email)
        setWebCookie(r, 'id', id)
        setWebCookie(r, 'name', user.name)
        result = APIResult(1, '', '')
    return jsonResult(r, result)

@post('/api/login')
def api_login(*, email, passwd, yzcode):
    r = web.Response()
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    if len(yzcode) > 0:
        if yzcode.lower() != config['verify'].lower():
            result = APIResult(0, '', '验证码错误')
        else:
            users = yield from User.findAll('email=?', [email])
            if len(users) > 0:
                sha1_passwd = '%s:%s' % ('hearain', passwd)
                passwd = hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest()
                if users[0].password == passwd:
                    # 设置session和cookie
                    config['_session'][email] = user2cookie(users[0], 86400)
                    setWebCookie(r, 'user', config['_session'][users[0].email])
                    setWebCookie(r, 'email', users[0].email)
                    setWebCookie(r, 'id', users[0].id)
                    setWebCookie(r, 'name', users[0].name)
                    result = APIResult(1, '', '')
                else:
                    result = APIResult(0, '', '密码错误')
            else:
                result = APIResult(0, '', '邮箱不存在')
    else:
        result = APIResult(0, '', '验证码错误')
    return jsonResult(r, result)

#获取文章的评论
@post('/api/commentList')
def api_commentList(*, page = 1):
    r = web.Response()
    num = yield from Comments.findNumber('count(id)')
    p = Page(num, int(page))
    if num == 0:
        data = dict(page=class_to_dict(p), blogs=())
    else:
        comments = yield from Comments.findAll(orderBy='create_time desc', limit=(p.offset, p.limit))
        data = dict(page=class_to_dict(p), blogs=comments)
    result = APIResult(1, data)
    return jsonResult(r, result)

#获取文章分类的api
@post('/api/getCategory')
def api_getCategory(*, request, page):
    r = web.Response()
    if (page is not None and len(page) > 0):
        num = yield from Category.findNumber('count(id)')
        p = Page(num, int(page))
        if num == 0:
            data = dict(page = class_to_dict(p), blogs = ())
        else:
            categorys = yield from Category.findAll(orderBy='create_time desc', limit=(p.offset, p.limit))
            data = dict(page=class_to_dict(p), blogs=categorys)
    else:
        categorys = yield from Category.findAll(orderBy='create_time desc')
        data = categorys
    result = APIResult(1, data)
    return jsonResult(r, result)

#获取文章列表
@post('/api/blogList')
def api_blogList(*, page = 1):
    r = web.Response()
    num = yield from Blogs.findNumber('count(id)')
    p = Page(num, int(page))
    if num == 0:
        data = dict(page = class_to_dict(p), blogs = ())
    else:
        blogs = yield from Blogs.findAll(orderBy = 'create_time desc', limit = (p.offset, p.limit))
        for row in blogs:
            #获取文章分类
            category_sql = ['%s %s' % ('select GROUP_CONCAT(B.id) category_id,GROUP_CONCAT(B.title) category_title from blog_category as A ',
            'left join category as B on A.category_id = B.id')]
            category_sql.append('where')
            category_sql.append('blog_id=?')
            category = yield from select(category_sql, [row.id])
            #获取标签分类
            tag_sql = ['%s %s' % ('select GROUP_CONCAT(B.id) tag_id,GROUP_CONCAT(B.title) tag_title from blog_tag as A',
                'left join tag as B on A.tag_id = B.id ')]
            tag_sql.append('where')
            tag_sql.append('blog_id=?')
            tag = yield from select(tag_sql, [row.id])
            #获取文章评论数
            comment_num = yield from Comments.findNumber('count(id)', 'display = 1 and blog_id=?', [row.id])
            if category[0].get('category_id') is not None:
                row.category_id = category[0].get('category_id').split(',')
            if category[0].get('category_title') is not None:
                row.category_title = category[0].get('category_title').split(',')
            if tag[0].get('tag_id') is not None:
                row.tag_id = tag[0].get('tag_id').split(',')
            if tag[0].get('tag_title') is not None:
                row.tag_title = tag[0].get('tag_title').split(',')
            row.comment_num = comment_num
        data = dict(page = class_to_dict(p), blogs = blogs)
    result = APIResult(1, data)
    return jsonResult(r, result)

#获取分类文章列表
@post('/api/category/blogList')
def api_category_blogList(*, page = 1, category_id):
    r = web.Response()
    num = yield from BlogCategory.findNumber('count(id)', 'category_id=?', [category_id])
    p = Page(num, int(page))
    if num == 0:
        data = dict(page = class_to_dict(p), blogs = ())
    else:
        blog_category_sql = ['select B.* from blog_category as A left join blogs as B on A.blog_id = B.id ']
        blog_category_sql.append('where')
        blog_category_sql.append('A.category_id = ?')
        blog_category_sql.append('order by B.create_time desc')
        blog_category_sql.append('limit ?,?')
        blogs = yield from select(blog_category_sql, [category_id, p.offset, p.limit])
        for row in blogs:
            #获取文章分类
            category_sql = ['%s %s' % ('select GROUP_CONCAT(B.id) category_id,GROUP_CONCAT(B.title) category_title from blog_category as A ',
            'left join category as B on A.category_id = B.id')]
            category_sql.append('where')
            category_sql.append('blog_id=?')
            category = yield from select(category_sql, [row['id']])
            #获取标签分类
            tag_sql = ['%s %s' % ('select GROUP_CONCAT(B.id) tag_id,GROUP_CONCAT(B.title) tag_title from blog_tag as A',
                'left join tag as B on A.tag_id = B.id ')]
            tag_sql.append('where')
            tag_sql.append('blog_id=?')
            tag = yield from select(tag_sql, [row['id']])
            #获取文章评论数
            comment_num = yield from Comments.findNumber('count(id)', 'display = 1 and blog_id=?', [row['id']])
            row['category_id'] = category[0].get('category_id').split(',')
            row['category_title'] = category[0].get('category_title').split(',')
            row['tag_id'] = tag[0].get('tag_id').split(',')
            row['tag_title'] = tag[0].get('tag_title').split(',')
            row['comment_num'] = comment_num
            for k in row:
                if isinstance(row[k], datetime.datetime):
                    row[k] = row[k].strftime('%Y-%m-%d %H:%M:%S')
        data = dict(page = class_to_dict(p), blogs = blogs)
    result = APIResult(1, data)
    return jsonResult(r, result)

#获取标签分类文章列表
@post('/api/tag/blogList')
def api_tag_blogList(*, page = 1, tag_id):
    r = web.Response()
    num = yield from BlogTag.findNumber('count(id)', 'tag_id=?', [tag_id])
    p = Page(num, int(page))
    if num == 0:
        data = dict(page = class_to_dict(p), blogs = ())
    else:
        blog_tag_sql = ['select B.* from blog_tag as A left join blogs as B on A.blog_id = B.id ']
        blog_tag_sql.append('where')
        blog_tag_sql.append('A.tag_id = ?')
        blog_tag_sql.append('order by B.create_time desc')
        blog_tag_sql.append('limit ?,?')
        blogs = yield from select(blog_tag_sql, [tag_id, p.offset, p.limit])
        for row in blogs:
            #获取文章分类
            category_sql = ['%s %s' % ('select GROUP_CONCAT(B.id) category_id,GROUP_CONCAT(B.title) category_title from blog_category as A ',
            'left join category as B on A.category_id = B.id')]
            category_sql.append('where')
            category_sql.append('blog_id=?')
            category = yield from select(category_sql, [row['id']])
            #获取标签分类
            tag_sql = ['%s %s' % ('select GROUP_CONCAT(B.id) tag_id,GROUP_CONCAT(B.title) tag_title from blog_tag as A',
                'left join tag as B on A.tag_id = B.id ')]
            tag_sql.append('where')
            tag_sql.append('blog_id=?')
            tag = yield from select(tag_sql, [row['id']])
            #获取文章评论数
            comment_num = yield from Comments.findNumber('count(id)', 'display = 1 and blog_id=?', [row['id']])
            row['category_id'] = category[0].get('category_id').split(',')
            row['category_title'] = category[0].get('category_title').split(',')
            row['tag_id'] = tag[0].get('tag_id').split(',')
            row['tag_title'] = tag[0].get('tag_title').split(',')
            row['comment_num'] = comment_num
            for k in row:
                if isinstance(row[k], datetime.datetime):
                    row[k] = row[k].strftime('%Y-%m-%d %H:%M:%S')
        data = dict(page = class_to_dict(p), blogs = blogs)
    result = APIResult(1, data)
    return jsonResult(r, result)

#发布文章
@post('/api/article/add')
@auth
def api_article_add(*, request, title, category, tag, content, summary):
    r = web.Response()
    blog = Blogs(title = title, user_id = getWebCookie(request, 'id'), summary = summary, content = content)
    id = yield from blog.save()
    category = urldecode(category)
    category = category[0].split(',')
    tags = tag.split('/')
    if id > 0:
        #文章分类插入
        for i in category:
            blog_category = BlogCategory(blog_id = id, category_id = i)
            blog_category_id = yield from blog_category.save()
        #标签分类插入
        for t in tags:
            t = t.strip()
            tag_title = yield from Tag.findAll('title=?', [t])
            #如果标签存在，则插入博客标签表，若不存在，则两张表都要插入
            if len(tag_title) > 0:
                tag_id = tag_title[0].get('id')
            else:
                tag = Tag(title = t)
                tag_id = yield from tag.save()
            blog_tag = BlogTag(blog_id = id, tag_id = tag_id)
            blog_tag_id = yield from blog_tag.save()
    if id > 0 and blog_category_id > 0 and blog_tag_id > 0:
        result = APIResult(1, '', '发布成功')
    else:
        result = APIResult(0, '', '发布失败')
    return jsonResult(r, result)

#编辑文章
@post('/api/article/edit')
@auth
def api_article_edit(*, request, id, title, category, tag, content, summary):
    r = web.Response()
    blog = yield from Blogs.findOne(id)
    blog = Blogs(id = id, title = title, summary = summary, content = content, update_time = currentTime(), create_time = blog.get('create_time'), user_id = blog.get('user_id'), view_count = blog.get('view_count'))
    result = yield from blog.update()
    category = urldecode(category)
    category = category[0].split(',')
    tags = tag.split('/')
    blog_category_id = 0
    blog_tag_id = 0
    if result > 0:
        #文章分类插入
        blog_category_sql = 'delete from blog_category where blog_id = ?'
        yield from execute(blog_category_sql, [id])
        blog_tag_sql = 'delete from blog_tag where blog_id = ?'
        yield from execute(blog_tag_sql, [id])

        for i in category:
            blog_category = BlogCategory(blog_id = id, category_id = i)
            blog_category_id = yield from blog_category.save()
        #标签分类插入
        for t in tags:
            t = t.strip()
            tag_title = yield from Tag.findAll('title=?', [t])
            #如果标签存在，则插入博客标签表，若不存在，则两张表都要插入
            if len(tag_title) > 0:
                tag_id = tag_title[0].get('id')
            else:
                tag = Tag(title = t)
                tag_id = yield from tag.save()
            blog_tag = BlogTag(blog_id = id, tag_id = tag_id)
            blog_tag_id = yield from blog_tag.save()
    if int(id) > 0 and int(blog_category_id) > 0 and int(blog_tag_id) > 0:
        result = APIResult(1, '', '修改成功')
    else:
        result = APIResult(0, '', '修改失败')
    return jsonResult(r, result)

#删除文章
@post('/api/article/delete')
@auth
def api_article_delete(*, request, article_id):
    r = web.Response()
    #删除文章表里面的数据
    blog = Blogs(id = article_id)
    blog_result = yield from blog.delete()
    #删除blog_tag表里面的数据
    blog_tag_sql = 'delete from blog_tag where blog_id = ?'
    yield from execute(blog_tag_sql, [article_id])
    #删除blog_category表里面的数据
    blog_category_sql = 'delete from blog_category where blog_id = ?'
    yield from execute(blog_category_sql, [article_id])
    if int(article_id) > 0 and int(blog_result) > 0:
        result = APIResult(1, '', '删除成功')
    else:
        result = APIResult(0, '', '删除失败')
    return jsonResult(r, result)

#添加文章分类
@post('/api/category/add')
@auth
def api_category_add(*, request, title):
    r = web.Response()
    category = yield from Category.findAll('title=?', [title])
    if len(category) > 0:
        result = APIResult(0, '', '该分类已存在')
    else:
        cate = Category(title = title)
        cate_id = yield  from cate.save()
        if cate_id > 0:
            result = APIResult(1, '', '分类添加成功')
        else:
            result = APIResult(0, '', '分类添加失败')
    return jsonResult(r, result)

#编辑文章分类
@post('/api/category/edit')
@auth
def api_article_edit(*, request, id, title):
    r = web.Response()
    cate = Category(id = id, title = title, create_time = currentTime(), is_delete = 0)
    result = yield from cate.update()
    if result is not None:
        result = APIResult(1, '', '修改成功')
    else:
        result = APIResult(0, '', '修改失败')
    return jsonResult(r, result)

#分类删除
@post('/api/category/delete')
@auth
def api_category_delete(*, request, category_id):
    r = web.Response()
    category = Category(id=category_id)
    category_result = yield from category.delete()
    if int(category_id) > 0 and int(category_result) > 0:
        result = APIResult(1, '', '删除成功')
    else:
        result = APIResult(0, '', '删除失败')
    return jsonResult(r, result)

#评论删除
@post('/api/comments/delete')
@auth
def api_comment_delete(*, request, comment_id):
    r = web.Response()
    # 删除文章的评论
    comment = Comments(id=comment_id)
    comment_result = yield from comment.delete()
    if int(comment_id) > 0 and int(comment_result) > 0:
        result = APIResult(1, '', '删除成功')
    else:
        result = APIResult(0, '', '删除失败')
    return jsonResult(r, result)

# 文章评论
@post('/api/comment/add')
def api_comment_add(*, request, comment, from_user_name, from_user_email, to_user_id, to_user_name, comment_parent, blog_id):
    r = web.Response()
    comment = Comments(blog_id = blog_id,
                       from_user_name = from_user_name,
                       from_user_email = from_user_email,
                       from_user_id = next_id(),
                       to_user_id = to_user_id,
                       to_user_name = to_user_name,
                       content = comment,
                       parent = comment_parent,
                       from_user_logo = 'http://www.gravatar.com/avatar/%s?d=wavatar&s=120' % hashlib.md5(from_user_email.encode('utf-8')).hexdigest()
                       )
    yield from comment.save()
    result = APIResult(1, '', '发布成功')
    #多线程发送邮件
    sendMailThread = emailThread('emailThread','博客评论', '<html><span style="color:red">%s</span>评论了您的博客，请查看<a href="http://localhost:9000/blog/%s#comment-%s">博客链接</html>' % (from_user_name, blog_id, comment.from_user_id))
    sendMailThread.start()
    return jsonResult(r, result)

#返回模板显示封装
def display(show = '', *kwargs):
    kw = dict(*kwargs)
    kw['__template__'] = '%s.html' % show
    return kw

#页面跳转
def redirect(value):
    return web.HTTPSeeOther(value)

