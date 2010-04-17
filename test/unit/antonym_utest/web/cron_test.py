from StringIO import StringIO
from unittest import main, TestCase

import mox

from google.appengine.api.labs import taskqueue
from google.appengine.ext import deferred

from antonym.model import Feed
from antonym.web.cron import CronIngestDriverHandler, CronIngestHandler, CronTwitterActorHandler, SafeTwitterActorHandler
from antonym.web.tweeter import TwitterConnector

from katapult.log import config as log_config
from katapult.mocks import MockEntity, MockKey, MockQuery

from antonym_utest.web import new_mock_request_response

class CronHandlersTest(TestCase):

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
        
        moxer.ReplayAll()
        handler = SafeTwitterActorHandler()
        handler.initialize(request, response)
        handler.post()
        moxer.VerifyAll()

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
    log_config()
    main()