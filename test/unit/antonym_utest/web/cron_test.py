from StringIO import StringIO
import traceback
from unittest import main, TestCase

from mox import IgnoreArg, Mox

from google.appengine.api.labs import taskqueue
from google.appengine.ext import deferred
from google.appengine.ext.webapp import util

import twitter

from antonym.accessors import ConfigurationAccessor
from antonym.web.activity import ActivityReporter
from antonym.model import Configuration, Feed
from antonym.web.cron import main as web_main, CronIngestDriverHandler, CronIngestHandler, CronTwitterActorHandler, SafeTwitterActorHandler
from antonym.web.tweeter import TwitterActor, TwitterConnector

from katapult.log import basic_config
from katapult.mocks import MockEntity, MockKey, MockQuery

from antonym_utest.web import new_mock_request_response


def _stub_taskqueue(moxer):
    moxer.StubOutWithMock(taskqueue, "add", use_mock_anything=True)

def _assert_handles_error(call):
    exc = call()
    print "handled: %s: %s" % (exc.__class__.__name__, exc)


class CronTwitterActorHandlerTest(TestCase):

    def test_main(self):
        moxer = Mox()
        moxer.StubOutWithMock(util, "run_wsgi_app")
        web_main()
        
    def test_cron_twitter_actor_handler(self):
        moxer = Mox()
        request, response = new_mock_request_response(moxer)
        
        _stub_taskqueue(moxer)
        
        taskqueue.add(url=IgnoreArg(), countdown=IgnoreArg())
        moxer.ReplayAll()
        handler = CronTwitterActorHandler()
        handler.initialize(request, response)
        handler.get()
        moxer.VerifyAll()


class SafeTwitterActorHandlerTest(TestCase):
    
    def test_safe_twitter_actor_handler(self):
        moxer = Mox()
        
        request, response = new_mock_request_response(moxer)
        
        moxer.StubOutWithMock(TwitterActor, "__new__")
        actor = moxer.CreateMock(TwitterActor)
        TwitterActor.__new__(TwitterActor).AndReturn(actor)
        actor.act()
        
        moxer.ReplayAll()
        handler = SafeTwitterActorHandler()
        handler.initialize(request, response)
        result = handler.post()
        moxer.VerifyAll()
        
        if result:
            exception, msg = result
            self.fail("exception occurred: %s" % msg)


class CronIngestDriverHandlerTest(TestCase):
    
    def test_get_registers_appropriate_tasks(self):
        moxer = Mox()
        request, response = new_mock_request_response(moxer)
        
        _stub_taskqueue(moxer)
        moxer.StubOutWithMock(Feed, "find_active", use_mock_anything=True)
        
        def create_call(i):
            source_name = "source-%i" % i
            source = MockEntity(key_name=source_name, name=source_name)
            return MockEntity(key_name="feed-%i" % i, artifact_source=source, url="hi")
        
        q_range = xrange(0,5)
        Feed.find_active().AndReturn(MockQuery(q_range, create_call=create_call))
        
        # expects queued tasks for each feed
        for i in q_range:
            taskqueue.add(name=IgnoreArg(), url=IgnoreArg())
        
        moxer.ReplayAll()
        handler = CronIngestDriverHandler()
        handler.initialize(request, response)
        handler.get()
        moxer.VerifyAll()


class CronIngestHandlerTest(TestCase):
    
    def test_post_handles_ingest_error(self):
        mox = Mox()
        request, response = new_mock_request_response(mox)
        mox.StubOutWithMock(Feed, "get_by_source_name")
        
        feed_name = "blah"
        Feed.get_by_source_name(feed_name, return_none=True).AndRaise(Exception("real bad"))
        
        handler = CronIngestHandler()
        handler.initialize(request, response)
        
        mox.ReplayAll()        
        _assert_handles_error(lambda: handler.post(feed_name))
        mox.VerifyAll()


if __name__ == "__main__":
    basic_config()
    main()