from unittest import main, TestCase

from mox import IgnoreArg, IsA, Mox
import twitter

from katapult.core import Record
from katapult.mocks import MockEntity

from antonym.accessors import ArtifactAccessor, ConfigurationAccessor, TwitterResponseAccessor
from antonym.model import ArtifactContent, Configuration, TwitterResponse
from antonym.mixer import Mixer
from antonym.ttwitter import ActionSelector, TweetAnalyzer, TwitterActor

from antonym_utest.text import create_content_list


def _create_default_mocks(moxer):
    """
    returns:
        twitter api
    """
    moxer.StubOutWithMock(TwitterResponseAccessor, "get_by_message_id")
    moxer.StubOutWithMock(TwitterResponseAccessor, "create")
    
    moxer.StubOutWithMock(ArtifactContent, "all")
    moxer.StubOutWithMock(ArtifactAccessor, "search")
    
    api = _create_api(moxer)
    
    return api

def _create_api(moxer):
    api = moxer.CreateMock(twitter.Api)
    return api

def _create_api_actor_and_selector(moxer):
    api = _create_default_mocks(moxer)
    _build_standard_config(moxer)
    bundle = _create_actor_and_delegates(api, moxer)
    bundle.api = api
    return bundle

def _create_actor_and_delegates(api, moxer):
    selector = moxer.CreateMock(ActionSelector)
    analyzer = moxer.CreateMock(TweetAnalyzer)
    actor = TwitterActor(selector=selector, twitter_api=api, reporter=Absorber(), analyzer=analyzer)
    return Record(actor=actor, selector=selector, analyzer=analyzer)

def _build_standard_config(moxer):
    moxer.StubOutWithMock(ConfigurationAccessor, "get_or_create")
    config = moxer.CreateMock(Configuration)
    ConfigurationAccessor.get_or_create().AndReturn(config)
    config.is_tweeting = None
    return config

def _no_messages(api, moxer):
    # no messages
    _return_direct_messages(api, [])
    _return_replies(api, [])
    
def _act_no_messages(api, moxer):
    _no_messages(api, moxer)
    
    _mix_random(api, moxer)
    
    api.PostUpdate(IsA(str)).AndReturn(Record(text="epic, fail is epic", user=Record(screen_name="jbell")))

def _mix_random(api, moxer):
    moxer.StubOutWithMock(Mixer, "mix_random_limit_sources")
    sources = [MockEntity(key_name=str(i), name="source/%d" % i) for i in xrange(2)]
    content = "so, wtf is going on here"
    Mixer.mix_random_limit_sources(2, degrade=True).AndReturn((sources, content))
    
    
def _no_direct_messages(api):
    _return_direct_messages(api, ())

def _return_direct_messages(api, directs):
    return api.GetDirectMessages(since=None).AndReturn(directs)

def _should_retweet(analyzer):
    analyzer.should_retweet(IgnoreArg()).AndReturn(True)
    
def _should_respond(analyzer, msg, condition):
    analyzer.should_respond(msg).AndReturn(condition)

def _no_response_found(msg):
    TwitterResponseAccessor.get_by_message_id(msg.id_str)

def _search_results(term, results):
    ArtifactAccessor.search(term).AndReturn(results)

def _mentions(api, *messages):
    _return_replies(api, messages)

def _return_replies(api, replies):
    return api.GetReplies(since=None).AndReturn(replies)

def _post_response_to(moxer, api, message):
    status = moxer.CreateMock(twitter.Status)
    status.id = message.id * 2
    status.id_str = str(status.id)
    api.PostUpdate(IgnoreArg(), message.id).AndReturn(status)
    return status

def _save_response(message, response):
    TwitterResponseAccessor.create(message.id_str,
        response_id=response.id_str,
        user=message.user.screen_name,
        tweet_type=TwitterResponse.MENTION)

def _format(msg):
    msg.AsDict().AndReturn({})
    
def _create_message(moxer, msg_id, username, text):
    msg = moxer.CreateMock(twitter.Status)        
    msg.id = msg_id
    msg.id_str = str(msg_id)
    msg.user = moxer.CreateMock(twitter.User)
    msg.user.screen_name = username
    msg.text = text
    return msg

def _fetch_trends(api):
    trends = ((Record(name="#universe"), Record(name="#interesting")), (Record(name="#explode"), Record(name="#whywhywhy")))
    api.GetTrendsDaily().AndReturn(trends)

def _should_act(selector, condition):
    selector.should_act().AndReturn(condition)

def _random_tweet(selector):
    selector.select_action().AndReturn(ActionSelector.RANDOM_TWEET)

def _trending(selector):
    _should_act(selector, True)
    selector.select_action().AndReturn(ActionSelector.TRENDING)

def _new_status():
    return Record(text="hi", user=Record(screen_name="mhawthorne"))


class Absorber:
    """ Receives messages but does nothing with them """
    def __getattr__(self, name):
        return lambda *args: Absorber()

    def __nonzero__(self):
        return True


class TwitterActorTest(TestCase):

    def test_act_no_messages(self):
        moxer = Mox()
        _build_standard_config(moxer)
        api = _create_api(moxer)
        _act_no_messages(api, moxer)
        
        bundle = _create_actor_and_delegates(api, moxer)
        actor, selector = bundle.actor, bundle.selector
        _should_act(selector, True)
        _random_tweet(selector)
        
        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()

    def test_act_direct_message(self):
        moxer = Mox()
        
        api = _create_default_mocks(moxer)
        _build_standard_config(moxer)
        bundle = _create_actor_and_delegates(api, moxer)
        actor = bundle.actor
        
        direct_id = 1
        direct = moxer.CreateMock(twitter.DirectMessage)
        user = moxer.CreateMock(twitter.User)
        direct.id = direct_id
        direct.sender_screen_name = "mikemattozzi"
        direct.text = "why is blood spattered all over your car?"
        
        _return_direct_messages(api, [direct])
        
        post = moxer.CreateMockAnything()
        post.id = 101
        
        _return_replies(api, ())
        TwitterResponseAccessor.get_by_message_id(str(direct_id))
        ArtifactAccessor.search("spattered").AndReturn(create_content_list(10))
        
        # response
        api.PostDirectMessage(direct.sender_screen_name, IgnoreArg()).AndReturn(post)
        TwitterResponseAccessor.create(str(direct.id), response_id=str(post.id), user=direct.sender_screen_name)
        post.AsDict().AndReturn({})
        
        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()

    def test_act_public_message(self):
        moxer = Mox()
        
        bundle = _create_api_actor_and_selector(moxer)
        api = bundle.api
        actor = bundle.actor
        analyzer = bundle.analyzer
        
        _no_direct_messages(api)

        msg = _create_message(moxer, 1, "mmattozzi", "@livelock why is blood spattered all over @mhawthorne's car?")
        
        _mentions(api, msg)
        
        _should_respond(analyzer, msg, True)
        _no_response_found(msg)
        _search_results("spattered", create_content_list(1))
        response = _post_response_to(moxer, api, msg) 
        _save_response(msg, response)
        _format(response)
        
        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()
    
    def test_act_responds_to_first_non_ignored_public_message(self):
        moxer = Mox()
        
        bundle = _create_api_actor_and_selector(moxer)
        api = bundle.api
        actor = bundle.actor
        selector = bundle.selector
        analyzer = bundle.analyzer
        
        _no_direct_messages(api)
        
        # this message should not be responded to.  livelock doesn't respond to retweets
        msg1 = _create_message(moxer, 1, "mhawthorne", "RT @livelock some random ass shit")
        
        # this message obviously warrants a response
        msg2 = _create_message(moxer, 2, "mmattozzi", "@livelock why is blood spattered all over @mhawthorne's car?")
        
        # messages are returned in reverse chronological order
        _mentions(api, msg2, msg1)

        # not responding and responding as appropriate
        _should_respond(analyzer, msg1, False)
        _should_respond(analyzer, msg2, True)
        
        _no_response_found(msg2)
        _search_results("spattered", create_content_list(1))
        response = _post_response_to(moxer, api, msg2)
        _save_response(msg2, response)
        _format(response)
        
        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()

       
    def _test_act_direct_and_response_with_direct_error(self):
        pass

    def __mock_config(self, config, moxer):
        moxer.StubOutWithMock(ConfigurationAccessor, "get_or_create")
        ConfigurationAccessor.get_or_create().AndReturn(config)
        
    def test_act_when_is_tweeting_not_set(self):
        moxer = Mox()

        config = moxer.CreateMock(Configuration)
        config.is_tweeting=None
        self.__mock_config(config, moxer)
        
        api = _create_api(moxer)
        _act_no_messages(api, moxer)
        bundle = _create_actor_and_delegates(api, moxer)
        actor, selector = bundle.actor, bundle.selector
        _should_act(selector, True)
        _random_tweet(selector)
        
        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()
        
    def test_act_when_is_tweeting_is_1(self):
        moxer = Mox()

        config = moxer.CreateMock(Configuration)
        config.is_tweeting="1"
        self.__mock_config(config, moxer)
                
        api = _create_api(moxer)
        _act_no_messages(api, moxer)
        bundle = _create_actor_and_delegates(api, moxer)
        actor, selector = bundle.actor, bundle.selector
        _should_act(selector, True)
        _random_tweet(selector)
        
        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()

    def test_act_when_is_tweeting_is_0(self):
        moxer = Mox()
        
        config = moxer.CreateMock(Configuration)
        config.is_tweeting="0"
        self.__mock_config(config, moxer)
        
        api = _create_api(moxer)
        actor = _create_actor_and_delegates(api, moxer).actor

        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()

    def test_act_when_is_tweeting_invalid(self):
        moxer = Mox()
        
        config = moxer.CreateMock(Configuration)
        config.is_tweeting="hello"
        self.__mock_config(config, moxer)        
        
        api = _create_api(moxer)
        bundle = _create_actor_and_delegates(api, moxer)
        actor, selector = bundle.actor, bundle.selector

        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()

    def test_retweet_not_previously_retweeted(self):
        moxer = Mox()
        
        api = _create_api(moxer)
        bundle = _create_actor_and_delegates(api, moxer)
        actor = bundle.actor
        analyzer = bundle.analyzer
        
        status_user = Record(screen_name=self.id())
        status_ids = [5, 10, 15]
        timeline = (Record(id=id, text="epic, fail is epic %s" % id, user=status_user) for id in status_ids)
        api.GetFriendsTimeline(count=10).AndReturn(timeline)
        # print "timeline: %s" % [t for t in timeline]
        
        # I choose a status to be the one I will retweet
        not_already_retweeted_id = status_ids[2]
        
        moxer.StubOutWithMock(TwitterResponseAccessor, "get_by_message_id")
        moxer.StubOutWithMock(TwitterResponseAccessor, "create")
        
        print "not_already_retweeted_id: %s " % not_already_retweeted_id
        for status_id in status_ids:
            print "status_id: %s" % status_id
            print "%s != %s == %s" % (status_id, not_already_retweeted_id, status_id != not_already_retweeted_id)
            
            if status_id != not_already_retweeted_id:
                # returns a result which means "already retweeted".  id is meaningless
                result = Record(message_id=status_id, response_id=status_id * 10)
                TwitterResponseAccessor.get_by_message_id(IsA(str)).AndReturn(result)
                print "returned %s for %s" % (result, status_id)
                continue
                
            # this status is the one I will retweet
            status_id_str = str(status_id)
            TwitterResponseAccessor.get_by_message_id(status_id_str)
            _should_retweet(analyzer)
            
            retweet_id = str(status_id + 1)
            retweet = Record(id=retweet_id, user=self.id())
            api.PostRetweet(status_id).AndReturn(retweet)
            TwitterResponseAccessor.create(status_id_str, response_id=retweet_id, tweet_type=TwitterResponse.RETWEET, user=status_user.screen_name)
                
        moxer.ReplayAll()
        actor.retweet()
        moxer.VerifyAll()

    def test_mix_trend(self):
        moxer = Mox()
        
        api = _create_api(moxer)
        bundle = _create_actor_and_delegates(api, moxer)
        actor = bundle.actor
        
        _fetch_trends(api)
        _mix_random(api, moxer)
        api.PostUpdate(IgnoreArg()).AndReturn(_new_status())
        
        moxer.ReplayAll()
        actor.mix_trend()
        moxer.VerifyAll()

    def test_act_mix_trend(self):
        moxer = Mox()
        
        api = _create_api(moxer)
        bundle = _create_actor_and_delegates(api, moxer)
        
        _build_standard_config(moxer)
        _no_messages(api, moxer)
        actor = bundle.actor
        selector = bundle.selector
        
        _trending(selector)
        
        moxer.StubOutWithMock(actor, "mix_trend")
        actor.mix_trend().AndReturn(_new_status())

        moxer.ReplayAll()
        actor.act()
        moxer.VerifyAll()


if __name__ == '__main__':
    basic_config()
    main()