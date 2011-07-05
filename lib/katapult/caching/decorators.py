import logging
import traceback

from katapult.caching import memcache_logging as memcache


def cache_return(key, **cache_kw):
    """ caching decorator """
    def function_wrapper(f):
        def args_wrapper(*args, **kw):
            value = memcache.get(key)
            if not value:
                value = f(*args, **kw)
                memcache.set(key, value, **cache_kw)
            return value
        return args_wrapper
    return function_wrapper


def cache_argument(pair_call, **kw_dec):
    """ 
    caching decorator.  caches method argument(s).
    
    if decorated function fails, no caching occurs.
    
    params:
        pair_call - function that generates key & value for cache
    keywords:
        time - cache TTL
    """
    cache_kw = {}
    time = kw_dec.pop("time", None)
    if time:
        cache_kw["time"] = time
    
    def function_wrapper(f):
        def args_wrapper(*args, **kw):
            key, value = pair_call(*args, **kw)
            return_value = f(*args, **kw)
            memcache.set(key, value, **cache_kw)
            return return_value
        return args_wrapper
    return function_wrapper


def cache_return_by_argument_key(key_call, **kw_dec):
    """ caching decorator, using an argument as part of the key """
    cache_kw = {}
    time = kw_dec.pop("time", None)
    if time:
        cache_kw["time"] = time
    
    def function_wrapper(f):
        def args_wrapper(*args, **kw):
            key = key_call(*args, **kw)
            refresh = kw.pop("refresh", False)
            value = memcache.get(key)
            if refresh or not value:
                value = f(*args, **kw)
                if value:
                    try:
                        memcache.set(key, value, **cache_kw)
                    except Exception, e:
                        logging.error(traceback.print_exc())
            return value
        return args_wrapper
    return function_wrapper


def cache_delete_by_argument_key(key_call):
    """ caching decorator.  if decorated function succeeeds, deletes key returned by key_call """
    def function_wrapper(f):
        def args_wrapper(*args, **kw):
            key = key_call(*args, **kw)
            value = f(*args, **kw)
            memcache.delete(key)
            return value
        return args_wrapper
    return function_wrapper

def cache_delete_by_argument_keys(key_call):
    """ caching decorator.  if decorated function succeeeds, deletes keys returned by key_call """
    def function_wrapper(f):
        def args_wrapper(*args, **kw):
            keys = key_call(*args, **kw)
            value = f(*args, **kw)
            for k in keys:
                memcache.delete(k)
            return value
        return args_wrapper
    return function_wrapper

def disable_cache_logging(f):
    """" decorator that disables cache logging for a method run """
    def arg_wrapper(*args, **kw):
        try:
            _logging_enabled(False)
            return f(*args, **kw)
        finally:
            _logging_enabled(True)
    return arg_wrapper
