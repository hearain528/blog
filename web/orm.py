import asyncio, aiomysql, logging, datetime,collections
logging.basicConfig(level=logging.INFO)

def log(sql, args=()):
	logging.info('SQL: %s' % sql)


@asyncio.coroutine
def create_pool(loop, **kw):
	logging.info('create databases connection pool...')
	global __pool
	try:
		__pool = yield from aiomysql.create_pool(
			host = kw.get('host','localhost'),
			port = kw.get('port', 3306),
			user = kw['user'],
			password = kw['password'],
			db = kw['db'],
			charset = kw.get('charset', 'utf8'),
			autocommit = kw.get('autocommit', True),
			maxsize = kw.get('maxsize', 10),
			minsize = kw.get('minsize', 1),
			loop = loop
		)
	except Exception as e:
		logging.error('connection pool is fail!!! \n\t error: %s' % e)

@asyncio.coroutine
def select(sql, args, size=None):
	log(sql, args)
	global __pool
	with(yield from __pool) as conn:
		cur = yield from conn.cursor(aiomysql.DictCursor)
		sql = ' '.join(sql)
		logging.info(sql.replace('?', '%s'))
		yield from cur.execute(sql.replace('?', '%s'), args or ())
		if size:
			rs = yield from cur.fetchmany(size)
		else:
			rs = yield from cur.fetchall()
		yield from cur.close()
		logging.info('rows return %s' % len(rs))
		return rs


@asyncio.coroutine
def execute(sql, args, autocommit=True):
	global __pool
	with(yield from __pool) as conn:
		if autocommit:
			yield from conn.begin()
		try:
			cur = yield from conn.cursor(aiomysql.DictCursor)
			sql = sql.replace('?', '%s')
			log(sql)
			yield from cur.execute(sql, args)
			affected = cur.rowcount
			if autocommit:
				yield from conn.commit()
			yield from cur.close()
		except Exception as e:
			if autocommit:
				yield from conn.rollback()
			raise Exception(e)
		return affected

def create_args_string(num):
	L = []
	for n in range(num):
		L.append('?')
	return ', '.join(L)


class Field(object):
	def __init__(self, name, column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default

	def __str__(self):
		return '<%s, %s, %s>' % (self.__class__.__name__, self.column_type, self.name)


#继承Field
#字符串映射Field
class StringField(Field):
	def __init__(self, name = None, primary_key = False, default = None, ddl = 'varchar(100)'):
		super().__init__(name, ddl, primary_key, default)

#Boolean类型
class BooleanField(Field):
	def __init__(self, name = None, default = 0):
		super().__init__(name, 'boolean', False, default)

class IntegerField(Field):
	def __init__(self, name = None, primary_key = False, default = 0):
		super().__init__(name, 'int', primary_key, default)

class FloatField(Field):
	def __init__(self, name = None, primary_key = False, default = 0.0):
		super().__init__(name, 'float', primary_key, default)

class DateTimeField(Field):
	def __init__(self, name = None, primary_key = False, default = ''):
		super().__init__(name, 'datetime', primary_key, default)

class TextField(Field):
	def __init__(self, name = None, default = None):
		super().__init__(name, 'text', False, default)

class ModelMetaclass(type):
	def __new__(cls, name, bases, attrs):
		if name == 'Model':
			return type.__new__(cls, name, bases, attrs)
		tableName = attrs.get('__table__', None) or name
		logging.info('found model: %s (table %s)' % (name, tableName))
		mappings = dict()
		fields = []
		primaryKey = None
		for k, v in attrs.items():
			if isinstance(v, Field):
				logging.info('found mapping: %s ==> %s' % (k, v))
				mappings[k] = v
				if v.primary_key:
					#找到主键
					if primaryKey:
						raise Exception('Duplicate primary key for field : %s' % k)
					primaryKey = k
				else:
					fields.append(k)
		if not primaryKey:
			raise Exception('Primary key not found..')
		for k in mappings.keys():
			attrs.pop(k)
		escaped_fields = list(map(lambda f: '`%s`' % f, fields))
		attrs['__mappings__'] = mappings
		attrs['__table__'] = tableName
		attrs['__primary_key__'] = primaryKey
		attrs['__fields__'] = fields
		attrs['__select__'] = 'select `%s`,%s from `%s`' % (primaryKey, ','.join(escaped_fields), tableName)
		attrs['__insert__'] = 'insert into `%s` (%s) values (%s)' % (tableName, ','.join(escaped_fields), create_args_string(len(escaped_fields)))
		attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
		attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
		return type.__new__(cls, name, bases, attrs)

class Model(dict, metaclass=ModelMetaclass):
	
	def __init__(self, **kw):
		super(Model, self).__init__(**kw)

	def __getattr__(self, item):
		try:
			return self[item]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s'" % item)

	def __setattr__(self, key, value):
		self[key] = value

	def getValue(self, key):
		return getattr(self, key, None)

	def getValueOrDefault(self, key):
		value = getattr(self, key, None)
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s: %s' % (key, str(value)))
				setattr(self, key, value)
		return value

	@classmethod
	@asyncio.coroutine
	def findAll(cls, where = None, args = None, **kw):
		sql = [cls.__select__]
		if where:
			sql.append('where')
			sql.append(where)
		if args is None:
			args = []
		orderBy = kw.get('orderBy', None)
		if orderBy:
			sql.append('order by')
			sql.append(orderBy)
		limit = kw.get('limit', None)
		if limit:
			sql.append('limit')
			if isinstance(limit, int):
				sql.append('?')
				args.append(limit)
			elif isinstance(limit, tuple) and len(limit) == 2:
				sql.append('?, ?')
				args.extend(limit)
			else:
				raise ValueError('Invalid limit value: %s' % str(limit))
		rs = yield from select(sql, args)
		for o in rs:
			for k in o:
				if isinstance(o[k], datetime.datetime):
					o[k] = o[k].strftime('%Y-%m-%d %H:%M:%S')
		return [cls(**r) for r in rs]

	@classmethod
	@asyncio.coroutine
	def findOne(cls, pk):
		sql = ['%s where `%s`=?' % (cls.__select__, cls.__primary_key__)]
		rs = yield from select(sql, [pk], 1)
		if len(rs) == 0:
			return None
		return rs[0]

	@classmethod
	@asyncio.coroutine
	def findNumber(cls, selectField, where = None, args = None):
		sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
		if where:
			sql.append('where')
			sql.append(where)
		rs = yield from select(sql, args, 1)
		if len(rs) == 0:
			return None
		return rs[0]['_num_']

	@classmethod
	@asyncio.coroutine
	def getId(cls):
		sql = ['select id from `%s` order by id desc' % (cls.__table__)]
		rs = yield from select(sql, None, 1)
		if len(rs) == 0:
			return None
		return rs[0]['id']

	@asyncio.coroutine
	def save(self):
		try:
			args = list(map(self.getValueOrDefault, self.__fields__))
			rows = yield from execute(self.__insert__, args)
			if rows != 1:
				logging.warn('failed to insert record: affected rows: %s' % rows)
			else:
				#返回插入之后的id
				# sql = ['select id from `%s` order by id desc' % (self.__table__)]
				id = yield from self.getId()
				return id
		except Exception as e:
			logging.error(e)

	@asyncio.coroutine
	def update(self):
		try:
			args = list(map(self.getValue, self.__fields__))
			args.append(self.getValue(self.__primary_key__))
			rows = yield from execute(self.__update__, args)
			if rows != 1:
				logging.warn('failed to update by primary key: affected rows: %s' % rows)
			else:
				return rows
		except Exception as e:
			logging.error(e)

	@asyncio.coroutine
	def delete(self):
		args = [self.getValueOrDefault(self.__primary_key__)]
		rows = yield from execute(self.__delete__, args)
		if rows != 1:
			logging.warn('failed to remove by primary key: affected rows: %s' % rows)
		else:
			return rows


class Page(object):
	def __init__(self, item_count, page_index = 1, page_size = 6):
		self.item_count = item_count #总数量
		self.page_size = page_size #每页的数量
		self.page_count = item_count // page_size + (1 if item_count % page_size > 0 else 0)
		if (item_count == 0) or (page_index > self.page_count):
			self.offset = 0
			self.limit = 0
			self.page_index = 1
		else:
			self.page_index = page_index
			self.offset = page_size * (page_index - 1)
			self.limit = self.page_size
		self.has_next = self.page_index < self.page_count
		self.has_previous = self.page_index > 1

	def __str__(self):
		return 'item_count: %s, page_count: %s, page_index: %s, page_size: %s, offset: %s, limit: %s' % (
		self.item_count, self.page_count, self.page_index, self.page_size, self.offset, self.limit)

	__repr__ = __str__