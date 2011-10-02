from StringIO import StringIO

from google.appengine.api import users

import twitter

from katapult.mocks import MockEntity

from antonym.ttwitter import TwitterConnector
from antonym.web.services import Services


def new_mock_request_response(moxer):
    """
    returns:
        mock (request, response) tuple
    """
    request = moxer.CreateMockAnything()
    
    response = moxer.CreateMockAnything()
    response.headers = {}
    response.out = StringIO()

    return request, response

def set_api_user(moxer):
    set_current_user(moxer, Services.API_USER)

def set_current_user(moxer, username):
    moxer.StubOutWithMock(users, "get_current_user", use_mock_anything=True)
    users.get_current_user().AndReturn(MockEntity(key_name=username, email=lambda: username))

def new_mock_twitter_api(moxer):
    moxer.StubOutWithMock(TwitterConnector, "new_api")
    api = moxer.CreateMock(twitter.Api)
    TwitterConnector.new_api().AndReturn(api)
    return api
