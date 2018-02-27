import functools
import logging
from functools import reduce

logging.basicConfig(level=logging.INFO)
#
# loop = asyncio.get_event_loop()
#
# async def test():
# 	try:
# 		await orm.create_pool(loop = loop, host='127.0.0.1', port=3306, user='root', password='', db='blog')
# 		user = User(name='Michael', email='18353367683', password='123456', admin=0, image='dd')
# 		await user.save()
# 	except Exception as e:
# 		logging.error(e)
#
# loop.run_until_complete(test())
import time
#
# def performance(f):
#     def fn(*args):
#         print(time.time)
#         return f(*args)
#     return fn
#
# @performance
# def factorial(n):
#     return reduce(lambda x,y: x*y, range(1, n+1))

def performance(unit):
	def perform_decorator(f):
		@functools.wraps(f)
		def wrapper(*args):
			logging.info('%s %s' % (time.time(), unit))
			return f(*args)
		wrapper.__name__ = f.__name__
		return wrapper
	return perform_decorator


@performance('ms')
def factorial(n):
	return reduce(lambda x, y: x * y, range(1, n + 1))



logging.info(factorial.__name__)

