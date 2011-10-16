from unittest import main, TestCase

from mox import IgnoreArg, Mox

import simplejson as json
from twitter import Api


class TwitterTest(TestCase):
    """ testing out a few code paths in the twitter client """
    
    def setUp(self):
        self.m = Mox()
        
    def tearDown(self):
        self.m.UnsetStubs()
        
    def test_retweet(self):
        api = Api(consumer_key="ckey", consumer_secret="csecret", 
            access_token_key="akey", access_token_secret="asecret")
        self.m.StubOutWithMock(api, "_FetchUrl")
        
        json_blob = json.dumps({})
        api._FetchUrl(IgnoreArg(), post_data=IgnoreArg()).AndReturn(json_blob)
        
        self.m.ReplayAll()
        api.PostRetweet(1)
        self.m.VerifyAll()

    def test_fetch_resource(self):
        api = Api(consumer_key="ckey", consumer_secret="csecret", 
            access_token_key="akey", access_token_secret="asecret")
        self.m.StubOutWithMock(api, "_FetchUrl")
        
        json_blob = json.dumps({})
        api._FetchUrl(IgnoreArg()).AndReturn(json_blob)
        
        self.m.ReplayAll()
        api.FetchResource("/trends/current.json")
        self.m.VerifyAll()

        
if __name__ == "__main__":
    main()