from unittest import main, TestCase

from google.appengine.api import memcache

from mox import IgnoreArg, Mox

from katapult.mocks import MockEntity

from antonym.accessors import ArtifactSourceAccessor, ConfigurationAccessor
from antonym.web.stats import StatsHandler

from antonym_utest.web import new_mock_request_response, new_mock_twitter_api, set_api_user


class StatsHandlerTest(TestCase):
    
    def setUp(self):
        self.m = Mox()
        
    def tearDown(self):
        self.m.UnsetStubs()
    
    def test_get(self):
        request, response = new_mock_request_response(self.m)
        self.m.StubOutWithMock(ArtifactSourceAccessor, "find_artifact_counts")
        self.m.StubOutWithMock(ArtifactSourceAccessor, "find_artifact_counts_newer")
        self.m.StubOutWithMock(memcache, "get_stats")
        self.m.StubOutWithMock(ConfigurationAccessor, "get_or_create")
        
        ArtifactSourceAccessor.find_artifact_counts().AndReturn({})
        ArtifactSourceAccessor.find_artifact_counts_newer(IgnoreArg()).AndReturn({})
        memcache.get_stats().AndReturn({})
        
        # token = "oauth_token_secret=hi&oauth_token=hi"
        # config = MockEntity(key_name="hi", twitter_oauth_enabled=True, twitter_access_token=token, twitter_read_only=False)
        # ConfigurationAccessor.get_or_create().AndReturn(config)

        api = new_mock_twitter_api(self.m)
        api.GetUserTimeline(count=IgnoreArg()).AndReturn(())
        api.GetDirectMessages(since=IgnoreArg()).AndReturn(())
        api.GetReplies(since=IgnoreArg()).AndReturn(())
                    
        handler = StatsHandler()
        handler.initialize(request, response)
        
        self.m.ReplayAll()
        handler.get()
        self.m.VerifyAll()


if __name__ == '__main__':
    basic_config()
    main()