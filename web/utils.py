import urllib.parse,time,json,logging,datetime,hashlib

#urldecode解码
def urldecode(data):
    return urllib.parse.parse_qs('data=' + data, encoding='utf-8').get('data')

#urlencode编码
def urlencode(data):
    return urllib.parse.urlencode(data).encode(encoding='utf-8')

#返回json数据
def jsonResult(r, data):
    r.content_type = 'application/json'
    r.body = json.dumps(class_to_dict(data), ensure_ascii=False).encode('utf-8')
    return r



#对象转化为json
def class_to_dict(obj):
    '''把对象(支持单个对象、list、set)转换成字典'''
    is_list = obj.__class__ == [].__class__
    is_set = obj.__class__ == set().__class__

    if is_list or is_set:
        obj_arr = []
        for o in obj:
            # 把Object对象转换成Dict对象
            dict = {}
            dict.update(o.__dict__)
            obj_arr.append(dict)
        return obj_arr
    else:
        dict = {}
        # for o in obj.data:
        #     for k in o:
        #         if isinstance(o[k], datetime.datetime):
        #             o[k] = o[k].strftime('%Y-%m-%d %H:%M:%S')
        dict.update(obj.__dict__)
        return dict

#设置cookie
def setWebCookie(r, key, value):
    r.set_cookie(key, value, max_age=86400, httponly=True)
#获取cookie
def getWebCookie(request, key):
    cookie_str = request.cookies.get(key)
    return cookie_str


# 计算加密cookie:
def user2cookie(user, max_age):
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s' % (user.email, user.password, expires)
    L = [expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)



