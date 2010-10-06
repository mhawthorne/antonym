from unittest import main, TestCase

from mox import Mox
from oauthtwitter import OAuthApi

from antonym.accessors import ConfigurationAccessor
from antonym.model import Configuration
from antonym.ttwitter import TwitterConnector, ReadOnlyTwitterApi


class TwitterConnectorTest(TestCase):
    
    def test_with_oauth(self):
        m = Mox()
        
        config = m.CreateMock(Configuration)
        config.twitter_access_token = "oauth_token=1234&oauth_token_secret=5678"
        config.twitter_read_only = False
        
        m.StubOutWithMock(ConfigurationAccessor, "get")
        ConfigurationAccessor.get().AndReturn(config)
        
        m.ReplayAll()
        api = TwitterConnector.new_api()
        self.__assert_is_instance(api, OAuthApi)
        m.VerifyAll()

    def test_mock(self):
        m = Mox()
        
        config = m.CreateMock(Configuration)
        config.twitter_access_token = "oauth_token=1234&oauth_token_secret=5678"
        
        m.StubOutWithMock(ConfigurationAccessor, "get")
        ConfigurationAccessor.get().AndReturn(config)
        
        m.ReplayAll()
        api = TwitterConnector.new_api()
        self.__assert_is_instance(api, ReadOnlyTwitterApi)
        m.VerifyAll()

    def __assert_is_instance(self, instance, klass):
        self.assert_(isinstance(instance, klass), "expected type: %s, found type: %s" % (klass.__name__, instance.__class__.__name__))


if __name__ == "__main__":
    main()