# -*- coding: utf-8 -*-
import sys, urllib.request, json, time
from collections import OrderedDict
from pyexcel_xls import get_data
from pyexcel_xls import save_data


#读取excel文件
def read_xls_file():
    xls_data = get_data(r"write1.xls")
    sheet_1 = xls_data.get('Sheet1')
    return sheet_1

def save_xls_file(insertData):
    data = OrderedDict()
    data.update({u"sheet": insertData})
    save_data("write2.xls", data)



#获取省份
def getProvince(cellphone):
    # url = 'http://apis.baidu.com/manyou/ip138/sjh?sjh=%s' % cellphone
    url = 'http://apis.juhe.cn/mobile/get?key=b4b88a8ffc09e2fd3f24251ee19fa168&phone=%s' % cellphone
    req = urllib.request.Request(url)

    # req.add_header("apikey", "34f8b935633f2e58a5c5aa72efb69c01")

    resp = urllib.request.urlopen(req)
    content = resp.read()
    if (content):
        data = content.decode('utf-8')
        data = json.loads(data)
        if data.get('result') is not None:
            return data.get('result')



sheet_1 = read_xls_file()
new_data = []
for i, row in enumerate(sheet_1):
    if i == 0:
        row.append('省')
        row.append('邮编')
        row.append('type')
        row.append('城市')
        row.append('areacode')
    if i > 0:
        time.sleep(1)
        print("第%s条" % i)
        data = getProvince(row[0])
        if isinstance(data, dict):
            row.append(data.get('province'))
            row.append(data.get('zip'))
            row.append(data.get('company'))
            row.append(data.get('city'))
            row.append(data.get('areacode'))
        new_data.append(row)
save_xls_file(new_data)

print('导出完毕')

