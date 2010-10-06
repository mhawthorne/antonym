from unittest import main, TestCase

from google.appengine.api import memcache

from mox import IsA, Mox

from katapult.caching import decorators


class DecoratorsTest(TestCase):
    
    def test_cache_return_by_argument_key_returns_on_memcache_error(self):
        m = Mox()
        m.StubOutWithMock(memcache, "get")
        m.StubOutWithMock(memcache, "set")
        
        val = 5
        def cached_call(id):
            return val
        decorated_call = decorators.cache_return_by_argument_key(lambda *args: "id:%s" % args[0])(cached_call)
        
        # value is not yet cached
        memcache.get(IsA(str))
        memcache.set(IsA(str), val).AndRaise(Exception("hi"))
        
        m.ReplayAll()
        val2 = decorated_call(self.id())
        m.VerifyAll()
        
        self.assertEquals(val, val2)


if __name__ == "__main__":
    main()