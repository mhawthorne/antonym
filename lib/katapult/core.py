from datetime import datetime, timedelta
import logging
import os
import os.path
import re
import time
import traceback

from wsgiref.handlers import format_date_time


class ApplicationException(Exception):
    """ Default exception from which all others can inherit """
    pass


class IllegalArgumentException(ApplicationException):
    pass


class NotImplementedException(ApplicationException):
    pass


class DataException(ApplicationException):
    pass


class NotFoundException(DataException):
    pass


def handle_error(f, error_call):
    try:
        f()
    except Exception, e:
        error_call(e)


def protect(f, **kw):
    """
    runs a function without raising any exceptions
    
    keywords:
        error_call
    """
    error_call = kw.pop("error_call")
    if not error_call:
        def error_call(e):
            logging.error(traceback.format_exc())

    handle_error(f, error_call)

def benchmark(f):
    with_args = False
    def args_wrapper(*args, **kwargs):
        t1 = time.time()
        res = f(*args, **kwargs)
        t2 = time.time()
        method_str = "%s(%s, %s)" % (f.func_name, args, kwargs) if with_args else f.func_name
        logging.debug('%s took %0.3fms' % (method_str, (t2-t1)*1000.0))
        return res
    return args_wrapper

# this randomly stopped working, why?
def benchmark_x():
    """ decorator that logs function time """
    #logging.debug("args:%s, kw:%s" % (args, kw))
    #with_args = kw.get("with_args", None)
    def function_wrapper(f):
        with_args = False
        def args_wrapper(*args, **kwargs):
            t1 = time.time()
            res = f(*args, **kwargs)
            t2 = time.time()
            method_str = "%s(%s, %s)" % (f.func_name, args, kwargs) if with_args else f.func_name
            logging.debug('%s took %0.3fms' % (method_str, (t2-t1)*1000.0))
            return res
        return args_wrapper
    return function_wrapper

def last_updated():
    path = __file__
    updated = None
    if os.path.exists(path):
        stat = os.stat(path)
        updated = datetime.fromtimestamp(stat.st_mtime)
    return updated


class Exceptions:
    
    @classmethod
    def format_last(cls):
        return traceback.format_exc()
        
    @classmethod
    def format(cls, exception):
        return "%s: %s" % (exception.__class__.__name__, exception)


class KeyCounter:
    """ Hash-like structure that keeps integer count for keys """
    
    def __init__(self):
        self.__hash = {}
        
    def reset(self, key):
        self.__hash[key] = 0
        
    def increment(self, key):
        count = self.__find_or_init(key)
        self.__hash[key] = count + 1
        
    def decrement(self, key):
        count = self.__find_or_init(key)
        self.__hash[key] = count - 1
        
    def __find_or_init(self, key):
        if not key in self.__hash:
            count = 0
        else:
            count = self.__hash[key]
        return count
        
    def count(self, key):
        return self.__hash.get(key, 0)

    def keys(self):
        return self.__hash.keys()
        
    def items(self):
        return self.__hash.items()

    def iteritems(self):
        return self.__hash.iteritems()

    def __repr__(self):
        return repr(self.__hash)


class Reference:
    """ Stores a mutable reference.  Useful for modifying external state inside of closures. """

    def __init__(self, value):
        self.__value = value

    def get(self):
        return self.__value

    def set(self, value):
        self.__value = value


class Record:
    """
    attribute container.
    """
    def __init__(self, **kw):
        self.__hash = {}
        self.set(**kw)

    def set(self, **kw):
        self.__hash.update(kw)
        for k, v in kw.iteritems():
            setattr(self, k, v)

    def has(self, key):
        return self.__hash.has_key(key)

    def to_hash(self):
        return self.__hash

    def __repr__(self):
        return repr(self.__hash)


class Hashes:
    """ Hash helpers """
    
    @classmethod
    def fetch_fields(cls, hash, fields, **kw):
        """
        params:
            hash
            fields - list of field names
        keywords:
            include_none - True if None values should be included for missing fields, instead of failure
        returns:
            object with attributes:
                missing_fields - list of missing fields (may be empty)
                values - list of values
        """
        include_none = kw.get("include_none", False)
        values = []
        missing = []
        result = HashFetchResult()
        for f in fields:
            if hash.has_key(f):
                result.add(f, hash[f])
            else:
                result.add_missing(f)
                if include_none:
                    result.add(f, None)
        return result

    @classmethod
    def missing_fields(cls, hash, fields, **kw):
        result = cls.fetch_fields(hash, fields, **kw)
        return result.missing_fields


class HashFetchResult:
    """
    attributes:
        hash
        values
        missing_fields
    see:
        Hashes.fetch_fields
    """
    def __init__(self):
        self.hash = {}
        self.values = []
        self.missing_fields = []

    def add_missing(self, field):
        self.missing_fields.append(field)
        
    def add(self, key, value):
        self.values.append(value)
        self.hash[key] = value