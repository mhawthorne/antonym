from unittest import main, TestCase

from google.appengine.api import memcache

from mox import IgnoreArg, Mox

from katapult.caching.queue import MemcacheQueue


class MemcacheQueueTest(TestCase):
    
    def test(self):
        """ this test is verifying that things are wired up correct.
            not testing any functionality.
        """
        m = Mox()
        m.StubOutWithMock(memcache, "get")
        m.StubOutWithMock(memcache, "set")
        m.StubOutWithMock(memcache, "get_multi")
        
        memcache.get(IgnoreArg())
        memcache.set(IgnoreArg(), IgnoreArg(), time=IgnoreArg())
        memcache.get_multi(IgnoreArg()).AndReturn({})
        
        m.ReplayAll()
        q = MemcacheQueue(self.id())
        q.items()
        m.VerifyAll()


if __name__ == "__main__":
    main()