from unittest import main, TestCase

from google.appengine.api import memcache

from mox import IgnoreArg, Mox

from antonym.web.activity import ActivityReporter


class ActivityReporterTest(TestCase):
    
    def test_posted(self):
        # TODO: shouldn't be mocking memcache, should be mocking MemcacheQueue.
        # but this is a good quick test
        m = Mox()
        m.StubOutWithMock(memcache, "incr")
        m.StubOutWithMock(memcache, "get")
        m.StubOutWithMock(memcache, "set")

        memcache.incr(IgnoreArg())
        memcache.get(IgnoreArg()).AndReturn(1)
        memcache.set(IgnoreArg(), IgnoreArg(), time=IgnoreArg())
        
        m.ReplayAll()
        ActivityReporter().posted("hi")
        m.VerifyAll()


if __name__ == "__main__":
    main()