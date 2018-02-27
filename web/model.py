import time, uuid, logging, datetime
logging.basicConfig(level=logging.INFO)

from orm import Model, IntegerField, StringField, BooleanField, FloatField, TextField, DateTimeField

def currentTime():
	return '%s' % datetime.datetime.now()

#用户表
class User(Model):
	__table__ = 'user'
	id = IntegerField(primary_key=True)
	name = StringField(ddl='varchar(50)')
	email = StringField(ddl='varchar(50)')
	password = StringField(ddl='varchar(50)')
	logo = StringField(ddl='varchar(500)')
	create_time = DateTimeField(default=currentTime)

#博客表
class Blogs(Model):
	__table__ = 'blogs'
	id = IntegerField(primary_key=True)
	title = StringField(ddl='varchar(50)')
	user_id = IntegerField()
	summary = StringField(ddl='varchar(200)')
	view_count = IntegerField()
	content = TextField()
	create_time = DateTimeField(default=currentTime)
	update_time = DateTimeField(default=currentTime)

#评论表
class Comments(Model):
	__table__ = 'comments'
	id = IntegerField(primary_key=True)
	blog_id = IntegerField()
	from_user_id = StringField(ddl='varchar(32)')
	from_user_name = StringField(ddl='varchar(50)')
	from_user_logo = StringField(ddl='varchar(500)')
	from_user_email = StringField(ddl='varchar(255)')
	to_user_id = StringField(ddl='varchar(32)')
	to_user_logo = StringField(ddl='varchar(500)')
	to_user_name = StringField(ddl='varchar(50)')
	to_user_email = StringField(ddl='varchar(255)')
	content = TextField()
	create_time = DateTimeField(default=currentTime)
	display = IntegerField(default=0)
	parent = IntegerField()

#文章分类表
class Category(Model):
	__table__ = 'category'
	id = IntegerField(primary_key=True)
	title = StringField(ddl='varchar(255)')
	create_time = DateTimeField(default=currentTime)
	is_delete = IntegerField(default=0)

#文章分类关联表
class BlogCategory(Model):
	__table__ = 'blog_category'
	id = IntegerField(primary_key=True)
	blog_id = IntegerField()
	category_id = IntegerField()
	create_time = DateTimeField(default=currentTime)

#标签表
class Tag(Model):
	__table__ = 'tag'
	id = IntegerField(primary_key=True)
	title = StringField(ddl='varchar(255)')
	create_time = DateTimeField(default=currentTime)

#博文标签关联表
class BlogTag(Model):
	__table__ = 'blog_tag'
	id = IntegerField(primary_key=True)
	blog_id = IntegerField()
	tag_id = IntegerField()
	create_time = DateTimeField(default=currentTime)








