from StringIO import StringIO
import traceback
from unittest import main, TestCase

import mox

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


class CronHandlersTest(TestCase):

    def test_main(self):
        moxer = mox.Mox()
        moxer.StubOutWithMock(util, "run_wsgi_app")
        web_main()
        
    def test_cron_twitter_actor_handler(self):
        moxer = mox.Mox()
        request, response = new_mock_request_response(moxer)
        
        self.__stub_taskqueue(moxer)
        
        taskqueue.add(url=mox.IgnoreArg(), countdown=mox.IgnoreArg())
        moxer.ReplayAll()
        handler = CronTwitterActorHandler()
        handler.initialize(request, response)
        handler.get()
        moxer.VerifyAll()

    def test_safe_twitter_actor_handler(self):
        moxer = mox.Mox()
        
        request, response = new_mock_request_response(moxer)
        
        # moxer.StubOutWithMock(ConfigurationAccessor, "get")
        # config = moxer.CreateMock(Configuration)
        # config.is_tweeting=True
        # ConfigurationAccessor.get().AndReturn(config)
        # 
        # moxer.StubOutWithMock(TwitterConnector, "new_api")
        # twitter_api = moxer.CreateMock(twitter.Api)
        # TwitterConnector.new_api().AndReturn(twitter_api)
        # 
        # moxer.StubOutWithMock(ActivityReporter, "__new__")
        # reporter = moxer.CreateMock(ActivityReporter)
        # ActivityReporter.__new__(ActivityReporter).AndReturn(reporter)
        # twitter_api.GetDirectMessages().AndReturn(())
        # twitter_api.GetReplies().AndReturn(())
        # reporter.did_not_act()
        
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

    def test_ingest_driver(self):
        moxer = mox.Mox()
        request, response = new_mock_request_response(moxer)
        
        self.__stub_taskqueue(moxer)
        moxer.StubOutWithMock(Feed, "find_active", use_mock_anything=True)
        
        def create_call(i):
            source_name = "source-%i" % i
            source = MockEntity(key_name=source_name, name=source_name)
            return MockEntity(key_name="feed-%i" % i, artifact_source=source, url="hi")
        
        q_range = xrange(0,5)
        Feed.find_active().AndReturn(MockQuery(q_range, create_call=create_call))
        
        # expects queued tasks for each feed
        for i in q_range:
            taskqueue.add(name=mox.IgnoreArg(), url=mox.IgnoreArg())
        
        moxer.ReplayAll()
        handler = CronIngestDriverHandler()
        handler.initialize(request, response)
        handler.get()
        moxer.VerifyAll()
        
    def __stub_taskqueue(self, moxer):
        moxer.StubOutWithMock(taskqueue, "add", use_mock_anything=True)
         
if __name__ == "__main__":
    basic_config()
    main()