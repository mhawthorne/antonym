""" interacts with memcache, logs results """

import logging

from google.appengine.api import memcache


_logging_enabled = True

    
def _logging_enabled(enabled):
    _logging_enabled = enabled

def _log(msg):
    if _logging_enabled:
        logging.debug(msg)

def get(key, **kw):
    value = memcache.get(key, **kw)
    action = "hit" if value else "miss"
    _log("cache get %s %s" % (action, key))
    return value

def get_multi(keys, **kw):
    values = memcache.get_multi(keys, **kw)
    
    value_len = len(values)
    key_len = len(keys)
    if value_len == key_len:
        action = "hit" 
    elif value_len and value_len < key_len:
        action = "partial-hit"
    else:
        action = "miss"

    _log("cache get_multi %s %s" % (action, keys))
    return values

def set(key, value, **kw):
    result = memcache.set(key, value, **kw)
    if result:
        action = "success"
    else:
        action = "error"
    _log("cache set %s %s" % (action, key))
    return result

def delete(key, **kw):
    result = memcache.delete(key, **kw)
    if result == 0:
        action = "error"
    elif result == 1:
        action = "miss"
    elif result == 2:
        action = "hit"
    _log("cache delete %s %s" % (action, key))
    return result

def delete_multi(keys, **kw):
    result = memcache.delete_multi(keys, **kw)
    if result:
        action = "success"
    else:
        action = "error"
    _log("cache delete_multi %s %s" % (action, keys))
    return result
    
def incr(key, **kw):
    result = memcache.incr(key, **kw)
    if result:
        action = "hit %s" % result
    else:
        action = "miss"
    _log("cache incr %s %s" % (action, key))
    return result

def decr(key, **kw):
    result = memcache.decr(key, **kw)
    if result:
        action = "hit %s" % result
    else:
        action = "miss"
    _log("cache decr %s %s" % (action, key))
    return result