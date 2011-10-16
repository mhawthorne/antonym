from unittest import main, TestCase

from mox import IgnoreArg, IsA, Mox, Regex
import twitter

from katapult.core import Record
from katapult.log import basic_config
from katapult.mocks import Mock, MockEntity, MockQuery

from antonym.accessors import ArtifactAccessor, ConfigurationAccessor, TwitterResponseAccessor
from antonym.model import ArtifactContent, Configuration, TwitterResponse
from antonym.web.tweeter import ActionSelector, TwitterActor, TwitterConnector, TwitterFriendHandler, TwitterUserHandler
from antonym.ttwitter import TweetAnalyzer

from antonym_utest.text import create_content_list
from antonym_utest.web import new_mock_request_response, set_api_user


def _create_api(moxer):
    api = moxer.CreateMock(twitter.Api)
    return api

class TwitterFriendHandlerTest(TestCase):
    
    def setUp(self):
        self.m = Mox()
        
    def tearDown(self):
        self.m.UnsetStubs()
    
    def test_put_friend(self):
        request, response = new_mock_request_response(self.m)
        self.m.StubOutWithMock(TwitterConnector, "new_api")
        
        api = _create_api(self.m)
        TwitterConnector.new_api().AndReturn(api)
        
        username = "mhawthorne"
        api.CreateFriendship(username)
        response.set_status(204)
        
        handler = TwitterFriendHandler()
        handler.initialize(request, response)
        set_api_user(self.m)        
        
        self.m.ReplayAll()
        handler.put(username)
        self.m.VerifyAll()
        
class TwitterUserHandlerTest(TestCase):
    
    def setUp(self):
        self.m = Mox()
        
    def tearDown(self):
        self.m.UnsetStubs()
    
    def test_put_friend(self):
        request, response = new_mock_request_response(self.m)
        self.m.StubOutWithMock(TwitterConnector, "new_api")
        
        api = _create_api(self.m)
        TwitterConnector.new_api().AndReturn(api)
        
        username = "mhawthorne"
        api.GetUser(username).AndReturn(Mock(name="hi", screen_name=username, 
            url="hi", statuses_count=1,
            followers_count=1, friends_count=1))
        
        handler = TwitterUserHandler()
        handler.initialize(request, response)
        set_api_user(self.m)        
        
        self.m.ReplayAll()
        handler.get(username)
        self.m.VerifyAll()
        
                
if __name__ == '__main__':
    basic_config()
    main()