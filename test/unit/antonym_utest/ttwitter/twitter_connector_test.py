from unittest import main, TestCase

from mox import Mox
# from oauthtwitter import OAuthApi
import twitter

from antonym.accessors import ConfigurationAccessor
from antonym.model import Configuration
from antonym.ttwitter import TwitterConnector, ReadOnlyTwitterApi


class TwitterConnectorTest(TestCase):
    
    def test_writable(self):
        m = Mox()
        
        config = m.CreateMock(Configuration)
        config.twitter_access_token = "oauth_token=1234&oauth_token_secret=5678"
        config.twitter_read_only = "0"
        
        m.StubOutWithMock(ConfigurationAccessor, "get_or_create")
        ConfigurationAccessor.get_or_create().AndReturn(config)
        
        m.ReplayAll()
        api = TwitterConnector.new_api()
        self.__assert_is_instance(api, twitter.Api)
        m.VerifyAll()

    def test_read_only(self):
        m = Mox()
        
        config = m.CreateMock(Configuration)
        config.twitter_access_token = "oauth_token=1234&oauth_token_secret=5678"
        config.twitter_read_only = "1"
        
        m.StubOutWithMock(ConfigurationAccessor, "get_or_create")
        ConfigurationAccessor.get_or_create().AndReturn(config)
        
        m.ReplayAll()
        api = TwitterConnector.new_api()
        self.__assert_is_instance(api, ReadOnlyTwitterApi)
        m.VerifyAll()

    def __assert_is_instance(self, instance, klass):
        self.assert_(isinstance(instance, klass), "expected type: %s, found type: %s" % (klass.__name__, instance.__class__.__name__))


if __name__ == "__main__":
    main()