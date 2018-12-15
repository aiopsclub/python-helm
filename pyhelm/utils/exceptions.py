#coding:utf-8
# 自定义异常类

class CustomError(Exception):
    def __init__(self, ErrorInfo):
        self.errorinfo = ErrorInfo
        Exception.__init__(self, ErrorInfo)

    def __str__(self):
        return self.errorinfo
