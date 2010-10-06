import logging

from katapult.caching import memcache_logging as memcache


class MemcacheQueue:
    
    def __init__(self, name, size=None, time=0):
        self.__default_expiration = time
        self.__name = name
        self.__ckey_prefix = "q=%s" % name
    
    def add(self, value):
        logging.debug("add %s" % str(value))
        memcache.incr(self.__max_index_key())
        ckey = self.__item_key(self.max_index())
        memcache.set(ckey, value, **self.__defaults())

    def remove(self):
        item_key = self.__item_key(self.max_index())
        value = memcache.get(item_key)
        if value:
            logging.debug("remove %s" % value)
            memcache.delete(item_key)
            memcache.decr(self.__max_index_key())
        return value

    def items(self):
        return self.__find_items(self.max_index())
        
    def clear(self):
        logging.debug("clear")
        memcache.delete(self.__max_index_key())
        memcache.delete_multi(self.__item_keys(self.max_index()))
    
    def scan(self, max_idx):
        return memcache.get_multi(self.__item_keys(max_idx))

    def __find_items(self, max_idx):
        # sorts items by key
        key_sorted_items = sorted(self.scan(max_idx).items(), key=lambda e: e[0])
        
        # returns values in key-sorted order
        return map(lambda e: e[1], key_sorted_items)
        
    def max_index(self):
        ckey = self.__max_index_key()
        v = memcache.get(ckey)
        if not v:
            v = 0
            memcache.set(ckey, v, **self.__defaults())
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