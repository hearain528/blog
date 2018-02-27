import csv
import datetime
import sys,io,re
from urllib import parse

from pymongo import MongoClient

#建立和数据库系统的连接,创建Connection时，指定host及port参数
client = MongoClient('120.26.42.204', 27017)

db = client.xiucai

db.authenticate("root","corn#2012")

collection = db.view_count


condition = dict({})

class TZ(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(minutes=-399)

begin = datetime.datetime(2017,2,2, tzinfo=TZ())
end = datetime.datetime(2017,2,24, tzinfo=TZ())

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')  # 改变标准输出的默认编码

def decode_referer(referer):
    referer = referer.decode('utf-8')
    reg = re.compile('@')
    referer = reg.sub('%', referer)
    referer = parse.unquote(referer)
    return referer

def exportPV(begin, end):
    rexExp = re.compile('^((?!xiucai).)+$')
    condition['recordDate'] = {"$gte": begin, "$lt": end}
    condition['referer'] = rexExp
    t = collection.find(condition)
    with open('egg.csv', 'w', newline='', encoding='utf-8') as csvfile:
        # csvfile.write(codecs.BOM_UTF8)
        spamwriter = csv.writer(csvfile)
        for x in  t:
            url = x.get('url')
            referer = x.get('referer').encode("utf-8")
            createTime = x.get('createTime') + datetime.timedelta(hours=8)
            spamwriter.writerow([url, decode_referer(referer), createTime])
    print("数据导出完毕")

exportPV(begin, end)