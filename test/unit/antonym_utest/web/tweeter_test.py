from unittest import main, TestCase

import mox
import twitter

from katapult.core import Record
from katapult.log import basic_config
from katapult.mocks import Mock, MockEntity, MockQuery

from antonym.accessors import ArtifactAccessor, ConfigurationAccessor, TwitterResponseAccessor
from antonym.mixer import Mixer
from antonym.model import ArtifactContent, Configuration
from antonym.web.tweeter import ActionSelector, TwitterActor, TwitterConnector

from antonym_utest.text import create_content_list


class Absorber:
    """ Receives messages but does nothing with them """
    def __getattr__(self, name):
        return lambda *args: Absorber()

    def __nonzero__(self):
        return True


def _create_content_list(count):
    return [_create_content(i) for i in xrange(count)]

def _create_content(content_id):
    source = MockEntity(key_name="m", name="mhawthorne")
    return MockEntity(key_name=source.name, source=source, source_name=source.name, body="content for %s" % content_id)

def _create_api(moxer):
    api = moxer.CreateMock(twitter.Api)
    # moxer.StubOutWithMock(TwitterConnector, "new_api")
    # TwitterConnector.new_api().AndReturn(api)
    return api
  
def _create_actor(api, moxer):
    selector = moxer.CreateMock(ActionSelector)
    # selector.should_act().AndReturn(True)
    # selector.select_action().AndReturn(ActionSelector.RANDOM_TWEET)
    actor = TwitterActor(selector, api, Absorber())
    # moxer.StubOutWithMock(actor, "__should_act")
    return actor, selector

def _create_default_mocks(moxer):
    """
    returns:
        twitter api
    """
    moxer.StubOutWithMock(TwitterResponseAccessor, "get_by_message_id")
    moxer.StubOutWithMock(TwitterResponseAccessor, "create")
    
    moxer.StubOutWithMock(ArtifactContent, "all")
    moxer.StubOutWithMock(ArtifactAccessor, "search")
    
    # TwitterActor.__should_act().AndReturn(True)
    api = _create_api(moxer)
    
    return api

def _build_standard_config(moxer):
    moxer.StubOutWithMock(ConfigurationAccessor, "get")
    config = moxer.CreateMock(Configuration)
    ConfigurationAccessor.get().AndReturn(config)
    config.is_tweeting = None
    # print "config.is_tweeting: %s" % config.is_tweeting
    return config
    
def _act_no_messages(api, moxer):
    moxer.StubOutWithMock(Mixer, "mix_random_limit_sources")
    
    # no messages
    api.GetDirectMessages().AndReturn([])
    api.GetReplies().AndReturn([])
    
    # ArtifactContent.all().AndReturn(MockQuery(xrange(0,10), create_call=_create_content))
    sources = [MockEntity(key_name=str(i), name="source/%d" % i) for i in xrange(2)]
    content = "so, wtf is going on here"
    Mixer.mix_random_limit_sources(2, degrade=True).AndReturn((sources, content))
    
    # TwitterConnector.new_api().AndReturn(api)
    api.PostUpdate(mox.IsA(str))

def _random_tweet(selector):
    selector.select_action().AndReturn(ActionSelector.RANDOM_TWEET)


class TwitterActorTest(TestCase):

    def test_act_no_messages(self):
        moxer = mox.Mox()
        _build_standard_config(moxer)
        api = _create_api(moxer)
        _act_no_messages(api, moxer)

        actor, selector = _create_actor(api, moxer)
        selector.should_act().AndReturn(True)
        _random_tweet(selector)
        
        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()

    def test_act_direct_message(self):
        moxer = mox.Mox()
        
        api = _create_default_mocks(moxer)
        _build_standard_config(moxer)
        actor, selector = _create_actor(api, moxer)
        # selector.should_act().AndReturn(True)
        
        direct_id = 1
        direct = moxer.CreateMock(twitter.DirectMessage)
        user = moxer.CreateMock(twitter.User)
        direct.id = direct_id
        direct.sender_screen_name = "mikemattozzi"
        direct.text = "why is blood spattered all over your car?"
        
        api.GetDirectMessages().AndReturn([direct])
        
        post = moxer.CreateMockAnything()
        post.id = 101
        
        api.GetReplies().AndReturn(())
        TwitterResponseAccessor.get_by_message_id(str(direct_id))
        ArtifactAccessor.search("spattered").AndReturn(create_content_list(10))
        
        # response
        api.PostDirectMessage(direct.sender_screen_name, mox.IgnoreArg()).AndReturn(post)
        TwitterResponseAccessor.create(str(direct.id), response_id=str(post.id), user=direct.sender_screen_name)
        post.AsDict().AndReturn({})
        
        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()

    def test_act_public_message(self):
        moxer = mox.Mox()
        
        api = _create_default_mocks(moxer)
        _build_standard_config(moxer)
        actor, selector = _create_actor(api, moxer)
        # selector.should_act().AndReturn(True)
        
        api.GetDirectMessages().AndReturn(())

        user = moxer.CreateMock(twitter.User)
        user.screen_name = "mikemattozzi"
        
        public_message = moxer.CreateMock(twitter.Status)        
        public_message.id = 1
        public_message.user = user
        
        public_message.text = "@livelock why is blood spattered all over @mhawthorne's car?"
        
        response = moxer.CreateMock(twitter.Status)
        response.id = 101
        
        api.GetReplies().AndReturn([public_message])
        TwitterResponseAccessor.get_by_message_id(str(public_message.id))
        ArtifactAccessor.search("spattered").AndReturn(create_content_list(10))                    
        
        # direct message to master
        # TwitterConnector.new_api().AndReturn(api)
        # api.PostDirectMessage("mhawthorne", mox.StrContains(user.screen_name))
        api.PostUpdate(mox.Regex("@mikemattozzi"), public_message.id).AndReturn(response) 
        TwitterResponseAccessor.create(str(public_message.id), response_id=str(response.id), user=user.screen_name)
        response.AsDict().AndReturn({})
        
        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()

    def _test_act_direct_and_response_with_direct_error(self):
        pass

    def test_act_when_is_tweeting_not_set(self):
        moxer = mox.Mox()

        config = moxer.CreateMock(Configuration)
        config.is_tweeting=None
        
        moxer.StubOutWithMock(ConfigurationAccessor, "get")
        ConfigurationAccessor.get().AndReturn(config)
        
        api = _create_api(moxer)
        _act_no_messages(api, moxer)
        actor, selector = _create_actor(api, moxer)
        selector.should_act().AndReturn(True)
        _random_tweet(selector)
        
        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()
        
    def test_act_when_is_tweeting_is_1(self):
        moxer = mox.Mox()

        config = moxer.CreateMock(Configuration)
        config.is_tweeting="1"
        
        moxer.StubOutWithMock(ConfigurationAccessor, "get")
        ConfigurationAccessor.get().AndReturn(config)
        
        api = _create_api(moxer)
        _act_no_messages(api, moxer)
        actor, selector = _create_actor(api, moxer)
        selector.should_act().AndReturn(True)
        _random_tweet(selector)
        
        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()

    def test_act_when_is_tweeting_is_0(self):
        moxer = mox.Mox()
        
        config = moxer.CreateMock(Configuration)
        config.is_tweeting="0"
        
        moxer.StubOutWithMock(ConfigurationAccessor, "get")
        ConfigurationAccessor.get().AndReturn(config)
        
        api = _create_api(moxer)
        actor, _ = _create_actor(api, moxer)

        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()

    def test_act_when_is_tweeting_invalid(self):
        moxer = mox.Mox()
        
        config = moxer.CreateMock(Configuration)
        config.is_tweeting="hello"
        
        moxer.StubOutWithMock(ConfigurationAccessor, "get")
        ConfigurationAccessor.get().AndReturn(config)
        
        api = _create_api(moxer)
        actor, selector = _create_actor(api, moxer)

        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()

    def test_retweet_not_previously_retweeted(self):
        moxer = mox.Mox()
        
        api = _create_api(moxer)
        actor, _ = _create_actor(api, moxer)
        
        status_ids = [5, 10, 15]
        api.GetFriendsTimeline(count=10).AndReturn((Record(id=id, text="epic, fail is epic %s" % id, user=Record(screen_name="jbell")) for id in status_ids))

        # I choose a status to be the one I will retweet
        not_retweeted_id = status_ids[2]
        
        moxer.StubOutWithMock(TwitterResponseAccessor, "get_by_message_id")
        
        for status_id in status_ids:
            print "status_id: %s" % status_id
            
            if status_id == not_retweeted_id:
                # this status is the one I will retweet
                TwitterResponseAccessor.get_by_message_id(status_id)
                api.PostRetweet(status_id)
            else:
                # returns a result which means "already retweeted".  id is meaningless
                TwitterResponseAccessor.get_by_message_id(mox.IsA(int)).AndReturn(Record(id=status_id * 2))
                
        moxer.ReplayAll()
        actor.retweet()
        moxer.VerifyAll()


if __name__ == '__main__':
    basic_config()
    main()