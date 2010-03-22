import logging
import re
import time
import traceback

import simplejson as json

from katapult.log import LoggerFactory


def time_request():
    """ decorator that logs request time by URL.  wraps appengine/WebObj RequestHandler methods. """
    def func_wrapper(f):
        def args_wrapper(*args, **kwargs):
            handler = args[0]
            t1 = time.time()
            res = f(*args, **kwargs)
            t2 = time.time()
            LoggerFactory.logger("request.timer").debug("url=%s time=%0.2fms" % (handler.request.path_qs, (t2-t1)*1000.0))
            return res
        return args_wrapper
    return func_wrapper


class RequestHelper:
    
    # params:
    #   handler - google.appengine.ext.webapp.RequestHandler
    def __init__(self, handler):
        self.__handler = handler

    def headers(self):
        return self.__handler.request.headers

    def header(self, name, value):
        self.__handler.response.headers[name] = value

    def error(self, status, message=None):
        self.__handler.error(status)
        if message:
            self.write(message)

    def write_json(self, obj):
        self.set_content_type('application/json')
        self.write(json.dumps(obj, indent=2))
          
    def write_text(self, msg):
        self.start_text()
        self.append_text(msg)

    def start_text(self):
        self.set_content_type('text/plain')
    
    def append_text(self, txt):
        self.write(txt)
        
    def write(self, msg):
        self.__handler.response.out.write("%s" % msg)

    def set_content_type(self, type):
        self.__handler.response.headers['Content-Type'] = type
       
    def set_status(self, status):
        self.__handler.response.set_status(status)


class RequestTimer(object):
    """ decorator that logs request time by URL """

    def __init__(self, function):
        self.__function = function

    def __call__(self, *args):
        t1 = time.time()
        res = self.__function(self.__request_handler, *args)
        t2 = time.time()
        logging.debug("url=%s time=%0.2fms" % (self.__request_handler.request.path_qs, (t2-t1)*1000.0))
        return res

    def __get__(self, instance, cls):
        self.__request_handler = instance
        return self
