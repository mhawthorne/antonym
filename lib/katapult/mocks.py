from katapult.core import IllegalArgumentException


class Mock:
    
    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)


class MockKey:
    
    def __init__(self, **kw):
        kid = kw.get("id", None)
        name = kw.get("name", None)
        
        # "is None" handles an id of 0, which is valid
        if not ((kid is not None) or name):
            raise IllegalArgumentException("keywords 'id' or 'name' must be provided")
        elif kid and name:
            raise IllegalArgumentException("both 'id' and 'name' cannot be provided")
            
        self.__id = kid if kid else None
        self.__name = name if name else None
        
    def id(self):
        return self.__id

    def name(self):
        return self.__name

    def __repr__(self):
        return "%s(id=%s, name=%s)" % (self.__class__.__name__, self.__id, self.__name)


class MockEntity:
    
    def __init__(self, **kw):
        key = kw.pop("key", None)
        key_name = kw.pop("key_name", None)
        
        if key:
            key = key
        elif key_name:
            key = MockKey(name=key_name)
        else:
            raise Exception("key or key_name keyword must be provided")
        
        self.__mock = Mock(key=key, **kw)        
        
    def __getattr__(self, name):
        return getattr(self.__mock, name)

    def __repr__(self):
        return "%s(key=%s)" % (self.__class__.__name__, self.key)


class MockQuery:
    
    def __init__(self, id_range, **kw):
        create_call = kw.get("create_call", None)
        self.__search_call = kw.get("search_call", None)
        keys_only = kw.get("keys_only", False)
        if not create_call:
            if keys_only:
                create_call = lambda i: MockKey(id=i)
            else:
                create_call = lambda i: MockEntity(key=MockKey(id=i))
            
        # only grabs first 1000 items
        if id_range:
            self.__set_items([create_call(id) for i, id in enumerate(id_range) if i < 1000])
        else:
            self.__set_items(())
        
        
    def count(self):
        return self.__count
        
    def order(self, order):
        return self
    
    def filter(self, template, value):
        return self

    def fetch(self, limit=1000, offset=0, **kw):
        # converts into iterator
        as_list = kw.get("as_list", False)
        items = self.__items[offset:offset+limit]
        return items if as_list else iter(items)

    def get(self):
        result = None
        if self.__items:
            result = self.__items[0]
        else:
            result = ()
        return result
    
    def search(self, term):
        if self.__search_call:
            self.__set_items(self.__search_call(term))
        else:
            self.__set_items(())
        return self

    def __set_items(self, items):
        if items is None: items = ()
        self.__items = items
        self.__count = len(self.__items)
        
    def __iter__(self):
        for item in self.__items:
            yield item
        
    def __getitem__(self, idx):
        if idx >= self.__count:
            raise Exception("index out of range (%s > %s)" % (idx, self.__count))
        return self.__items[idx]
        
