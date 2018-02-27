import csv
import datetime,time
import sys,io,re
from urllib import request,parse
import json


#获取时间
def getDate(begin, i):
    oneday = datetime.timedelta(days=i)
    yesterday = begin - oneday
    return yesterday

begin = datetime.datetime(2017,1,3)

baseurl = 'http://tongji.xiucai.com/BIAnalyticsService/r/service/statistic/'

#编码
def urlEncode(data):
    return parse.quote(json.dumps(data))

#解码
def urlDecode(data):
    data = parse.unquote(bytes.decode(data), 'utf-8')
    data = json.loads(data)
    return data

#请求数据
def getRequestData(url):
    try:
        data = request.urlopen(url)
        print(data.info())
        return data.read()
    except request.HTTPError as e:
        print(e.getcode())
        print(e.reason)
        print(e.geturl())
        print("-------------------------")
        print(e.info())


def getCanalRegisterSourceResult(startDate, endDate):
    apiUrl = baseurl + "getCanalRegisterSourceResult/"
    params = {'startDate': startDate, 'endDate': endDate, 'source_id':None, 'first_id':0,'second_id':0}
    apiUrl = apiUrl + urlEncode(params)
    data = getRequestData(apiUrl)
    time.sleep(2)
    data = urlDecode(data)
    data = data.get('data').get('data')
    sourceData = dict(
    registerCount = 0,
    pv = 0,
    uv = 0,
    orderMoney = 0,
    registerOrderCount = 0,
    effectiveRegisterCount = 0,
    orderCount = 0,
    fullRegisterCount = 0)
    for i in data:
        if i.get('registerCount') is not None:
            sourceData['registerCount'] += int(i.get('registerCount'))
        else:
            sourceData['registerCount'] += 0
        if i.get('pv') is not None:
            sourceData['pv'] += int(i.get('pv'))
        else:
            sourceData['pv'] += 0
        if i.get('uv') is not None:
            sourceData['uv'] += int(i.get('uv'))
        else:
            sourceData['uv'] += 0
        if i.get('registerOrderCount') is not None:
            sourceData['registerOrderCount'] += int(i.get('registerOrderCount'))
        else:
            sourceData['registerOrderCount'] += 0
        if i.get('effectiveRegisterCount') is not None:
            sourceData['effectiveRegisterCount'] += int(i.get('effectiveRegisterCount'))
        else:
            sourceData['effectiveRegisterCount'] += 0
        if i.get('orderCount') is not None:
            sourceData['orderCount'] += int(i.get('orderCount'))
        else:
            sourceData['orderCount'] += 0
        if i.get('fullRegisterCount') is not None:
            sourceData['fullRegisterCount'] += int(i.get('fullRegisterCount'))
        else:
            sourceData['fullRegisterCount'] += 0
    return sourceData

#获取pv
def getPageViewResult(startDate, endDate):
    apiUrl = baseurl + "getPageViewResult/"
    params = {'startDate': startDate, 'endDate': endDate}
    apiUrl = apiUrl + urlEncode(params)
    data = getRequestData(apiUrl)
    time.sleep(2)
    data = urlDecode(data)
    allpv = 0
    for i in data.get('data'):
        allpv += int(i.get('all'))
    return allpv

#获取uv
def getUserViewResult(startDate, endDate):
    apiUrl = baseurl + "getUserViewResult/"
    params = {'startDate': startDate, 'endDate': endDate}
    apiUrl = apiUrl + urlEncode(params)
    data = getRequestData(apiUrl)
    time.sleep(2)
    data = urlDecode(data)
    alluv = 0
    for i in data.get('data'):
        alluv += int(i.get('all'))
    return alluv

#获取注册数
def getUserRegisterResult(startDate, endDate):
    apiUrl = baseurl + "getUserRegisterResult/"
    params = {'startDate': startDate, 'endDate': endDate}
    apiUrl = apiUrl + urlEncode(params)
    result = getRequestData(apiUrl)
    time.sleep(2)
    result = urlDecode(result)
    print(result)
    data = dict(
        allRegisterCount=0,
        allFullRegisterCount = 0,
        allEffectiveRegisterCount = 0
    )
    for i in result.get('data'):
        data['allRegisterCount'] += int(i.get('all'))
        data['allFullRegisterCount'] += int(i.get('allFullRegisterCount'))
        data['allEffectiveRegisterCount'] += int(i.get('allEffectiveRegisterCount'))
    return data

#获取订单数
def getBaseOrderResult(startDate, endDate):
    apiUrl = baseurl + "getBaseOrderResult/"
    params = {'startDate': startDate, 'endDate': endDate}
    apiUrl = apiUrl + urlEncode(params)
    result = getRequestData(apiUrl)
    time.sleep(2)
    result = urlDecode(result)
    data = dict(
        allOrderCount = 0,
        allOrderMoney = 0,
        allRegisterOrderCount = 0
    )
    for i in result.get('data').get('data'):
        if int(i.get('orderType')) == 4:
            data['allOrderCount'] += int(i.get('count'))
            data['allOrderMoney'] += int(i.get('money'))
    data['allRegisterOrderCount'] = result.get('data').get('registerOrderCount')
    return data


with open('egg2.csv', 'w', newline='', encoding='utf-8') as csvfile:
    # csvfile.write(codecs.BOM_UTF8)
    spamwriter = csv.writer(csvfile)
    for i in range(1, 10):
        startDate = getDate(begin, i).strftime('%Y-%m-%d')
        endDate = getDate(begin, i - 1).strftime('%Y-%m-%d')
        source_data = getCanalRegisterSourceResult(startDate, endDate)

        pv_data = getPageViewResult(startDate, startDate)

        uv_data = getUserViewResult(startDate, startDate)

        register_data = getUserRegisterResult(startDate, startDate)

        order_data = getBaseOrderResult(startDate, endDate)
        pv = pv_data - int(source_data.get('pv'))
        uv = uv_data - int(source_data.get('uv'))
        registerCount = int(register_data.get('allRegisterCount')) - int(source_data.get('registerCount'))
        fullRegisterCount = int(register_data.get('allFullRegisterCount')) - int(
            source_data.get('fullRegisterCount'))
        effectiveRegisterCount = int(register_data.get('allEffectiveRegisterCount')) - int(
            source_data.get('effectiveRegisterCount'))
        orderCount = int(order_data.get('allOrderCount')) - int(source_data.get('orderCount'))
        registerOrderCount = int(order_data.get('allRegisterOrderCount')) - int(
            source_data.get('registerOrderCount'))
        spamwriter.writerow([startDate, pv, uv, registerCount, fullRegisterCount, effectiveRegisterCount, orderCount, registerOrderCount])
        print('%s数据导出完毕' % startDate)
    print("全部数据导出完毕")
