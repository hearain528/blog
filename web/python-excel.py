# -*- coding: utf-8 -*-
from collections import OrderedDict
from pyexcel_xls import get_data
from pyexcel_xls import save_data
import aiomysql
import asyncio

import web.conf.config

#读取excel文件
def read_xls_file():
    xls_data = get_data(r"source.xls")
    sheet_1 = xls_data.get('Sheet1')
    return sheet_1

def save_xls_file(insertData):
    data = OrderedDict()
    data.update({u"sheet": insertData})
    save_data("write.xls", data)


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
        charset='utf8',
        autocommit=db.get('autocommit', True),
        maxsize=db.get('maxsize', 10),
        minsize=db.get('minsize', 1),
        loop=loop
    )
    with(yield from pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        sheet_1 = read_xls_file()
        new_data = []
        for i, row in enumerate(sheet_1):
            if i == 0:
                row.append('昵称')
                row.append('公司')
                row.append('手机号')
                row.append('职位')
            if i > 0:
                sql = "select cellphone,nickname,company,position from xc_member where email='%s'" % (row[0])
                yield from cur.execute(sql, None)
                rs = yield from cur.fetchall()
                if isinstance(rs, list):
                    row.append(rs[0].get('nickname'))
                    row.append(rs[0].get('company'))
                    row.append(rs[0].get('cellphone'))
                    row.append(rs[0].get('position'))
            new_data.append(row)
        save_xls_file(new_data)

#取数据
loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()