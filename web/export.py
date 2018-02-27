import aiomysql
import asyncio
import csv
import logging
import datetime
from array import array

from pymongo import MongoClient

import web.conf.config

#建立和数据库系统的连接,创建Connection时，指定host及port参数
client = MongoClient('120.26.42.204', 27017)

db = client.xiucai

db.authenticate("root","corn#2012")

collection = db.view_count


condition = dict({})

class TZ(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(minutes=-399)

begin = datetime.datetime(2017,2,27, tzinfo=TZ())
end = datetime.datetime(2017,3,29, tzinfo=TZ())


#注册登录留存率
def isLogin(begin, end, userIds):
    print("注册数：%d" % len(userIds))
    condition['recordDate'] = {"$gte": begin, "$lt": end}
    condition['userId'] = {"$in": userIds}
    t = collection.find(condition)
    active_userIds = []
    for x in t:
        if x.get('userId') not in active_userIds:
            active_userIds.append(x.get('userId'))
    print("登录数: %d" % len(active_userIds))

def getVipLogin(begin, end, cur):
    condition['recordDate'] = {"$gte": begin, "$lt": end}
    condition['userId'] = {"$gt": 0}
    t = collection.find(condition)
    login_user = []
    for x in t:
        if x.get('userId') not in login_user:
            login_user.append(x.get('userId'))
            yield from cur.execute(
                'select vip_level from xc_member where create_time >= "2016-12-01" and create_time < "2017-01-01" and ifnull(is_vest,0) = 0' % x.get('userId'),
                None)
            rs = yield from cur.fetchOne()
            print(rs)
    return login_user

# for i in range((end - begin).days):
#         day = begin + datetime.timedelta(days=i)
#         day_two = day + datetime.timedelta(days=i + 1)
#         condition['recordDate'] = {"$gte": day, "$lt": day_two}
#         t = collection.find(condition)
            # print(j)

userIds = []


#从mysql里面取出数据
@asyncio.coroutine
def init(loop):
    db = web.conf.config.config.get('xiucai_db')
    pool = yield from aiomysql.create_pool(
        host=db.get('host', 'localhost'),
        port=db.get('port', 3306),
        user=db['user'],
        password=db['password'],
        db=db['db'],
        autocommit=db.get('autocommit', True),
        maxsize=db.get('maxsize', 10),
        minsize=db.get('minsize', 1),
        loop=loop
    )
    with(yield from pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        condition['recordDate'] = {"$gte": begin, "$lt": end}
        condition['userId'] = {"$gt": 0}
        t = collection.find(condition)
        count = 0
        login_user = []
        for x in t:
            if x.get('userId') not in login_user:
                login_user.append(x.get('userId'))
                yield from cur.execute(
                    'select vip_level from xc_member where ifnull(is_vest,0) = 0 and id=%s' % str(x.get(
                        'userId')),
                    None)
                rs = yield from cur.fetchone()
                if rs is not None:
                    if rs.get('vip_level') == 400:
                        count = count + 1
        print("总共会员登录数：%s" % count)
        # yield from cur.execute('select id from xc_member where create_time >= "2016-12-01" and create_time < "2017-01-01" and ifnull(is_vest,0) = 0', None)
        # rs = yield from cur.fetchall()
        # for row in rs:
        #     if row.get('id') not in userIds:
        #         id = row.get('id')
        #         userIds.append(id)
        # isLogin(begin, end, tuple(userIds))
        # escaped_fields = list(map(lambda f: '`%s`' % f, userIds))
        # strIds = ','.join(str(x) for x in userIds)
        # yield from cur.execute('select email from xc_member where length(email) > 0 and ifnull(is_vest, 0) = 0 and id in (%s)' % strIds, None)
        # emails = yield from cur.fetchall()
        # with open('egg.csv', 'w', newline='') as csvfile:
        #     spamwriter = csv.writer(csvfile)
        #     for email in emails:
        #         spamwriter.writerow([email.get('email')])
        # yield from cur.close()
        # logging.info('++++++++++++++++++++')




#取数据
loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()






# content = database.course_user_info_history.find()
# #打印所有数据
# for i in content:
#     print(i)


