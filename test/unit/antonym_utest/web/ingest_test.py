from unittest import main, TestCase

import mox

from google.appengine.api import users
from google.appengine.api.users import User

import antonym
import antonym.model
from antonym.model import ArtifactContent, ArtifactInfo, ArtifactSource, Feed
from antonym.web.ingest import IngestHandler
from antonym.web.services import Services

from katapult.mocks import MockEntity, MockKey, MockQuery

from antonym_utest.web import new_mock_request_response


class IngestHandlerTest(TestCase):

    def _test_post_invalid_source(self):
        moxer = mox.Mox()
        
        request, response = new_mock_request_response(moxer)
        
        source_name = "hi"
        
        @staticmethod
        def get_by_source_name(name, **result_kw):
            return None
        #Feed.get_by_source_name = get_by_source_name
        
        handler = IngestHandler()
        handler.initialize(request, response)
        
        moxer.ReplayAll()
        handler.post(source_name)
        response.set_status(404)
        moxer.VerifyAll()

    def test_post_unauthorized(self):
        moxer = mox.Mox()
        
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
        moxer = mox.Mox()
        
        request, response = new_mock_request_response(moxer)
        moxer.StubOutWithMock(users, "get_current_user", use_mock_anything=True)
        moxer.StubOutWithMock(Feed, "get_by_source_name", use_mock_anything=True)
        
        source_name = "hi"
        username = Services.API_USER
        user = MockEntity(key_name=username, email=lambda: username)
        
        users.get_current_user().AndReturn(user)
        handler = IngestHandler()
        users.get_current_user().AndReturn(user)
        handler.initialize(request, response)
        Feed.get_by_source_name(source_name, return_none=True).AndReturn(MockEntity(key_name=source_name, url="no"))
        
        moxer.ReplayAll()
        handler.post(source_name)
        moxer.VerifyAll()

    def test_post_no_user(self):
        moxer = mox.Mox()
        
        request, response = new_mock_request_response(moxer)
        moxer.StubOutWithMock(users, "get_current_user", use_mock_anything=True)
        moxer.StubOutWithMock(User, "__init__", use_mock_anything=True)
        moxer.StubOutWithMock(Feed, "get_by_source_name", use_mock_anything=True)
        
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
        Feed.get_by_source_name(source_name, return_none=True).AndReturn(MockEntity(key_name=source_name, url="no"))
        
        moxer.ReplayAll()
        handler.post(source_name)
        moxer.VerifyAll()

if __name__ == "__main__":
    main()