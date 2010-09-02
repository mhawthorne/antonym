import logging

from google.appengine.api import memcache

from katapult.log import LoggerFactory

# TODO: share code between cache decorators

def cache_return(key, **cache_kw):
    """ caching decorator """
    def function_wrapper(f):
        def args_wrapper(*args, **kw):
            value = Cache.get(key)
            if not value:
                value = f(*args, **kw)
                Cache.set(key, value, **cache_kw)
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
            Cache.set(key, value, **cache_kw)
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
            refresh = kw.get("refresh", False)
            value = Cache.get(key)
            if refresh or not value:
                value = f(*args, **kw)
                if value:
                    Cache.set(key, value, **cache_kw)
            return value
        return args_wrapper
    return function_wrapper


def cache_delete_by_argument_key(key_call):
    """ caching decorator.  if decorated function succeeeds, deletes key returned by key_call """
    def function_wrapper(f):
        def args_wrapper(*args, **kw):
            key = key_call(*args, **kw)
            value = f(*args, **kw)
            Cache.delete(key)
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
                Cache.delete(k)
            return value
        return args_wrapper
    return function_wrapper

def disable_cache_logging(f):
    """" decorator that disables cache logging for a method run """
    def arg_wrapper(*args, **kw):
        try:
            Cache.logging_enabled(False)
            return f(*args, **kw)
        finally:
            Cache.logging_enabled(True)
    return arg_wrapper


class Cache:
    """ interacts with memcache, logs results """
    
    __logging_enabled = True
    
    @classmethod
    def logging_enabled(cls, enabled):
        cls.__logging_enabled = enabled
     
    @classmethod
    def __log(cls, msg):
        if cls.__logging_enabled:
            logging.debug(msg)
            
    @classmethod
    def get(cls, key, **kw):
        value = memcache.get(key, **kw)
        action = "hit" if value else "miss"
        cls.__log("cache get %s %s" % (action, key))
        return value

    @classmethod
    def get_multi(cls, keys, **kw):
        values = memcache.get_multi(keys, **kw)
        
        value_len = len(values)
        key_len = len(keys)
        if value_len == key_len:
            action = "hit" 
        elif value_len and value_len < key_len:
            action = "partial-hit"
        else:
            action = "miss"

        cls.__log("cache get_multi %s %s" % (action, keys))
        return values

    @classmethod
    def set(cls, key, value, **kw):
        result = memcache.set(key, value, **kw)
        if result:
            action = "success"
        else:
            action = "error"
        cls.__log("cache set %s %s" % (action, key))
        return result
    
    @classmethod
    def delete(cls, key, **kw):
        result = memcache.delete(key, **kw)
        if result == 0:
            action = "error"
        elif result == 1:
            action = "miss"
        elif result == 2:
            action = "hit"
        cls.__log("cache delete %s %s" % (action, key))
        return result
    
    @classmethod
    def delete_multi(cls, keys, **kw):
        result = memcache.delete_multi(keys, **kw)
        if result:
            action = "success"
        else:
            action = "error"
        cls.__log("cache delete_multi %s %s" % (action, keys))
        return result
        
    @classmethod
    def incr(cls, key, **kw):
        result = memcache.incr(key, **kw)
        if result:
            action = "hit %s" % result
        else:
            action = "miss"
        cls.__log("cache incr %s %s" % (action, key))
        return result

    @classmethod
    def decr(cls, key, **kw):
        result = memcache.decr(key, **kw)
        if result:
            action = "hit %s" % result
        else:
            action = "miss"
        cls.__log("cache decr %s %s" % (action, key))
        return result

class MemcacheQueue:
    
    def __init__(self, name, size=None, time=0):
        self.__default_expiration = time
        self.__name = name
        self.__ckey_prefix = "q=%s" % name
    
    def add(self, value):
        logging.debug("add %s" % str(value))
        Cache.incr(self.__max_index_key())
        ckey = self.__item_key(self.max_index())
        Cache.set(ckey, value, **self.__defaults())

    def remove(self):
        item_key = self.__item_key(self.max_index())
        value = Cache.get(item_key)
        if value:
            logging.debug("remove %s" % value)
            Cache.delete(item_key)
            Cache.decr(self.__max_index_key())
        return value

    def items(self):
        return self.__find_items(self.max_index())
        
    def clear(self):
        logging.debug("clear")
        Cache.delete(self.__max_index_key())
        Cache.delete_multi(self.__item_keys(self.max_index()))
    
    def scan(self, max_idx):
        return Cache.get_multi(self.__item_keys(max_idx))

    def __find_items(self, max_idx):
        # sorts items by key
        key_sorted_items = sorted(self.scan(self.max_index()).items(), key=lambda e: e[0])
        
        # returns values in key-sorted order
        return map(lambda e: e[1], key_sorted_items)
        
    def max_index(self):
        ckey = self.__max_index_key()
        v = Cache.get(ckey)
        if not v:
            v = 0
            Cache.set(ckey, v, **self.__defaults())
        return v

    def __defaults(self):
        return dict(time=self.__default_expiration)
        
    def __item_keys(self, max_idx):
        return [self.__item_key(i) for i in range(max_idx + 1)]
        
    def __max_index_key(self):
        return self.__build_key("max-index")
        
    def __item_key(self, index):
        return self.__build_key("item=%03d" % index)
        
    def __build_key(self, ckey):
        return "%s;%s" % (self.__ckey_prefix, ckey)

    def __repr__(self):
        return "%s[%s]" % (self.__class__.__name__, self.__name)