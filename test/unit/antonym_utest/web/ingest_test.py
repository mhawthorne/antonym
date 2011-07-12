from unittest import main, TestCase

from mox import IgnoreArg, Mox

from google.appengine.api import users
from google.appengine.api.users import User

from katapult.accessors.counters import Counter

from antonym.accessors import Counters
from antonym.ingest import model
import antonym.model
from antonym.model import ArtifactContent, ArtifactInfo, ArtifactSource, Feed
from antonym.web.ingest import IngestHandler
from antonym.web.services import Services

from katapult.mocks import MockEntity, MockKey, MockQuery

from antonym_utest.web import new_mock_request_response


class IngestHandlerTest(TestCase):

    def test_post_unauthorized(self):
        moxer = Mox()
        
        request, response = new_mock_request_response(moxer)
        moxer.StubOutWithMock(users, "get_current_user", use_mock_anything=True)
        
        handler = IngestHandler()
        handler.initialize(request, response)
        username = "bad.user"
        users.get_current_user().AndReturn(MockEntity(key_name=username, email=lambda: username))
        response.set_status(403)     
        response.clear()
        
        moxer.ReplayAll()
        handler.post("hi")
        moxer.VerifyAll()
        
    def test_post_with_user(self):
        moxer = Mox()
        
        request, response = new_mock_request_response(moxer)
        moxer.StubOutWithMock(users, "get_current_user", use_mock_anything=True)
        moxer.StubOutWithMock(ArtifactInfo, "delete_oldest_by_source", use_mock_anything=True)
        moxer.StubOutWithMock(Counters, "source_counter")
        moxer.StubOutWithMock(Feed, "get_by_source_name", use_mock_anything=True)
        moxer.StubOutWithMock(model, "ingest_feed_entries")
        
        source_name = "hi"
        username = Services.API_USER
        user = MockEntity(key_name=username, email=lambda: username)
        
        users.get_current_user().AndReturn(user)
        handler = IngestHandler()
        users.get_current_user().AndReturn(user)
        handler.initialize(request, response)
        request.get("keep").AndReturn(None)
        
        counter = moxer.CreateMock(Counter)
        Counters.source_counter(source_name).AndReturn(counter)
        counter.decrement(IgnoreArg())
        
        source = MockEntity(key_name=source_name, name=source_name)
        feed = MockEntity(key_name=source_name, url="no", artifact_source=source)
        ArtifactInfo.delete_oldest_by_source(source, IgnoreArg()).AndReturn([])
        
        Feed.get_by_source_name(source_name, return_none=True).AndReturn(feed)
        model.ingest_feed_entries(feed, user, error_call=IgnoreArg()).AndReturn(())
        
        moxer.ReplayAll()
        handler.post(source_name)
        moxer.VerifyAll()

    def _test_post_no_user(self):
        moxer = Mox()
        
        request, response = new_mock_request_response(moxer)
        moxer.StubOutWithMock(users, "get_current_user", use_mock_anything=True)
        moxer.StubOutWithMock(User, "__init__", use_mock_anything=True)
        moxer.StubOutWithMock(Feed, "get_by_source_name", use_mock_anything=True)
        moxer.StubOutWithMock(model, "ingest_feed_entries")
        
        source_name = "hi"
        username = Services.API_USER
        user = MockEntity(key_name=username, email=lambda: username)
        
        # passes auth (via cron)
        users.get_current_user().AndReturn(user)
        handler = IngestHandler()
        # no logged in user
        users.get_current_user()
        User.__init__(username)
        handler.initialize(request, response)
        feed = MockEntity(key_name=source_name, url="no")
        Feed.get_by_source_name(source_name, return_none=True).AndReturn(feed)
        model.ingest_feed_entries(feed, None, error_call=IgnoreArg()).AndReturn(())
        
        moxer.ReplayAll()
        handler.post(source_name)
        moxer.VerifyAll()


if __name__ == "__main__":
    main()