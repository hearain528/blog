#接口返回的数据
class APIResult(object):
    def __init__(self, status, data='', message=''):
        self.status = status
        self.data = data
        self.message = message

#上传文件返回的数据
class APIUploadResult(object):
    def __init__(self, status, message = '', url = ''):
        self.success = status
        self.message = message
        self.url = url

#定义API的错误
class APIError(Exception):
    def __init__(self, error, data='', message=''):
        super(APIError, self).__init__(message)
        self.error = error
        self.data = data
        self.message = message

class APIValueError(APIError):
    def __init__(self, field, message=''):
        super(APIValueError, self).__init__('value:invalid', field, message)

class APIResourceNotFoundError(APIError):
    '''
    Indicate the resource was not found. The data specifies the resource name.
    '''
    def __init__(self, field, message=''):
        super(APIResourceNotFoundError, self).__init__('value:notfound', field, message)

class APIPermissionError(APIError):
    '''
    Indicate the api has no permission.
    '''
    def __init__(self, message=''):
        super(APIPermissionError, self).__init__('permission:forbidden', 'permission', message)
