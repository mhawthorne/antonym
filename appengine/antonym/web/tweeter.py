from datetime import datetime
import logging
import random
import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from oauth.oauth import OAuthToken
from oauthtwitter import OAuthApi
import simplejson as json
import twitter

from antonym.accessors import ConfigurationAccessor, TwitterResponseAccessor
from antonym.core import AppException, IllegalStateException
from antonym.mixer import Mixer
from antonym.text.speakers import new_random_speaker
from antonym.text.speakers.core import SentenceSpeaker
from antonym.text.speakers.graph import NxGraphSpeaker
from antonym.text.tweeting import parse_tweet
from antonym.web.activity import ActivityReporter
from antonym.web.services import require_service_user
from antonym.web import service_users
from antonym import rrandom

from katapult.core import Record
from katapult.log import basic_config
from katapult.numbers import safe_int
from katapult.requests import RequestHelper


def user_hash(user):
    """ converts a twitter.User to a hash, including only properties I care about. """
    user_hash = { 'name': user.name, 
        'screen-name': user.screen_name, 
        'url': user.url,
        'statuses-count': user.statuses_count,
        'followers-count': user.followers_count,
        'friends-count': user.friends_count }
        
    if user.friends_count > 0:
        # converts to a string to avoid weird long decimals
        user_hash['follower-to-friend-ratio'] = str(round(float(user.followers_count) / float(user.friends_count), 2))
    
    return user_hash

def sorted_user_list(users):
    return sorted(users, key=lambda u: u['screen-name'])

def new_default_mixer():
    return Mixer.new(new_speaker())

def describe_status(status):
    return "%s: %s" % (status.user.screen_name, status.text)


class MockTwitterApi:

    __supported_methods = set(["GetDirectMessages", "GetFriendsTimeline", "GetReplies"])
    
    def __init__(self, delegate=None):
        self.__d = delegate or TwitterConnector.new_api()
        self.__reporter = ActivityReporter()
        self.__post_id = 1;

    def PostUpdate(self, *args):
        msg = args[0]
        self.__post_id += 1;
        r = Record(id=self.__post_id)
        r.AsDict = lambda: r.to_hash()
        return r
        
    def __getattr__(self, name):
        logging.debug("%s.%s" % (self.__class__.__name__, name))
        if name in self.__supported_methods and hasattr(self.__d, name):
            return getattr(self.__d, name)
        else:
           raise IllegalStateException("%s.%s not found" % (self.__class__.__name__, name)) 
              
    def __nonzero__(self):
        return True


class TwitterConnector:
    
    @classmethod
    def new_api(cls):
        config = ConfigurationAccessor.get()
        if config and config.twitter_oauth_enabled and config.twitter_access_token:
            logging.debug("creating oauth API instance")
            return cls._new_oauth_api(OAuthToken.from_string(config.twitter_access_token))
        else:
            logging.debug("creating basic API instance")
            return cls._new_basic_api()
        
    @classmethod
    def _new_basic_api(cls):
        # TODO: use memcache?
        u, p = service_users.twitter_default_creds()
        return twitter.Api(username=u, password=p, cache=None)

    @classmethod
    def get_request_token_and_auth_url(cls):
        key, secret = service_users.twitter_oauth_creds()
        api = OAuthApi(key, secret, cache=None)
        request_token = api.getRequestToken()
        return request_token, api.getAuthorizationURL(request_token)

    @classmethod
    def get_access_token(cls, request_token_key, request_token_secret):
        key, secret = service_users.twitter_oauth_creds()
        api = OAuthApi(key, secret, OAuthToken(request_token_key, request_token_secret), cache=None)
        return api.getAccessToken()

    @classmethod
    def _new_oauth_api(cls, twitter_access_token):
        key, secret = service_users.twitter_oauth_creds()
        return OAuthApi(key, secret, twitter_access_token, cache=None)


class TwitterFollowersHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self):
        # friend to follower ratio, used to find non-spam followers
        ff_ratio = self.request.get("ratio")
        
        helper = RequestHelper(self)
        t_api = TwitterConnector.new_api()
        
        filtered_followers = ([user_hash(u) for u in t_api.GetFollowers()])
        if ff_ratio:
            filtered_followers = filter(lambda u: u['follower-to-friend-ratio'] > float(ff_ratio), 
                filtered_followers)
            
        followers = sorted_user_list(filtered_followers)
        helper.write_json(followers)


class TwitterFriendsHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self):
        helper = RequestHelper(self)
        t_api = TwitterConnector.new_api()
        friends = sorted_user_list([user_hash(u) for u in t_api.GetFriends()])
        helper.write_json(friends)


class TwitterFriendHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self, username):
        helper = RequestHelper(self)
        t_api = TwitterConnector.new_api()
        friends = t_api.GetFriends()
        found = None
        for f in friends:
            if f.screen_name == username:
                found = f
                break
        result = {}
        result['friend'] = True if found else False
        helper.write_json(result)
    
    @require_service_user()
    def put(self, username):
        """ follows the specified user """
        helper = RequestHelper(self)
        t_api = TwitterConnector.new_api()
        t_api.CreateFriendship(username)
        helper.set_status(204)
        
    @require_service_user()
    def delete(self, username):
        """ unfollows the specified user """
        helper = RequestHelper(self)
        t_api = TwitterConnector.new_api()
        t_api.DestroyFriendship(username)
        helper.set_status(204)


class TwitterResponseHandler(webapp.RequestHandler):
    
    @require_service_user()
    def post(self):
        TwitterWebActor.respond(self)


class TwitterDirectHandler(webapp.RequestHandler):
    
    @require_service_user()
    def post(self):
        helper = RequestHelper(self)
        
        if not len(self.request.body):
            helper.error(400, "body required")
            return
            
        decoded_body = urllib.unquote(self.request.body)
        t_api = TwitterConnector.new_api()
        status = t_api.PostUpdate(decoded_body)
        helper.write_json(status.AsDict())


class TwitterMixHandler(webapp.RequestHandler):
    
    @require_service_user()
    def post(self):
        TwitterActor.mix(self)


class TwitterActorHandler(webapp.RequestHandler):
    
    @require_service_user()
    def post(self):
        TwitterWebActor.act(self)


class TwitterUserHandler(webapp.RequestHandler):
  
    @require_service_user()
    def get(self, username):
        helper = RequestHelper(self)
        t_api = TwitterConnector.new_api()
        user = t_api.GetUser(username)
        helper.write_json(user_hash(user))


class TwitterFriendsTimelineHandler(webapp.RequestHandler):
  
    @require_service_user()
    def get(self):
        helper = RequestHelper(self)
        t_api = TwitterConnector.new_api()
        statuses = [s.AsDict() for s in t_api.GetFriendsTimeline()]
        helper.write_json(statuses)


class ActionSelector:
    
    # detailed actions
    NOTHING = "nothing"
    RESPONSE = "response"
    RANDOM_TWEET = "random-tweet"
    RETWEET = "retweet"
    
    # keys are UTC hour ranges, values are lists of tuples containing (action, weight) pairs
    # this is used to select what to do at a given time
    # do stuff from 7am-12am EST = 11am-4am UTC
    # relax from 12am-7am EST = 4am-11am UTC
    _active_weights = [(True, 5), (False, 5)]
    _passive_weights = [(True, 1), (False, 9)]
        
    # maps time of day to weights
    _times_to_weights = { xrange(0, 4): _active_weights, 
        xrange(4,11): _passive_weights,
        xrange(11,24): _active_weights }

    # weighted probabilities of actions to perform if there is nothing to respond to
    _actions_weighted = [(RANDOM_TWEET,5), (RETWEET,5)]

    def should_act(self):
        now = datetime.utcnow()
        # TODO: optimize range search
        logging.debug("time: %s" % now)
        should_act = False
        for hour_range, actions in self._times_to_weights.iteritems():
            if now.hour in hour_range:
                logging.debug("actions: %s" % actions)
                should_act = rrandom.select_weighted_with_replacement(actions)
                break
        return should_act

    def select_action(self):
        return rrandom.select_weighted_with_replacement(self._actions_weighted)


class TwitterActor(object):
    
    MASTER_USERNAME = "mhawthorne"
        
    def __init__(self, selector=None, twitter_api=None, reporter=None):
        self.__selector = selector or ActionSelector()
        self.__twitter = twitter_api or TwitterConnector.new_api()
        self.__reporter = reporter or ActivityReporter()

    def __select_speaker(self):
        speaker_name, speaker = new_random_speaker()
        logging.debug("selected speaker: %s" % speaker.__class__.__name__)
        return speaker
        
    def mix(self):
        """
        returns:
            twitter.Status
        """
        speaker = self.__select_speaker()
        sources, content = Mixer.new(speaker).mix_random_limit_sources(2, degrade=True)
        logging.debug("mixing random tweet: {%s} %s" % (";".join([s.name for s in sources]), content))
        self.__reporter.posted(content)
        return self.__twitter.PostUpdate(content)
        
    def messages(self):
        """
        returns:
            list of twitter.Status
        """
        # I use list comprehensions since I suspect that these methods return iterators
        # reversing the lists puts them in chronological order
        directs = [m for m in self.__twitter.GetDirectMessages()]
        directs.reverse()
        
        replies = [r for r in self.__twitter.GetReplies()]
        replies.reverse()
        
        return directs, replies
        
    def respond(self):
        directs, responses = self.messages()

        direct = None
        response = None
        
        try:
            direct = self.__direct_response(directs)
        except AppException, e:
            logging.error(e)
        
        try:
            response = self.__public_response(responses)
        except AppException, e:
            logging.error(e)
        
        return direct, response

    def retweet(self):
        # loads all statuses into map so I can remove them if I've already retweeted
        statuses = {}
        for status in self.__twitter.GetFriendsTimeline(count=10):
            statuses[status.id] = status

        while statuses:
            _, retweet_source = statuses.popitem()
            
            # TODO: should query for type=retweet
            # otherwise I may retweet a mention
            
            # checks if status has been retweeted
            response = TwitterResponseAccessor.get_by_message_id(retweet_source.id)
            
            # if msg was already retweeted, removed from set and let loop continue
            if not response:
                break
            else:
                logging.debug("found retweet for message %s" % response.id)
                
        pretty_retweet = describe_status(retweet_source)
        logging.debug("retweeting '%s'" % pretty_retweet)
        self.__twitter.PostRetweet(retweet_source.id)
        self.__reporter.retweeted(pretty_retweet)
        return retweet_source, pretty_retweet
        
    def act(self, force_act=False, action=None, skip_responses=False):
        """
        returns:
            (action, response) tuple.  response type depends on the action that was performed.
        """        
        if not force_act:
            config = ConfigurationAccessor.get()
            if config and (config.is_tweeting is not None) and (not safe_int(config.is_tweeting)):
                logging.debug("config.is_tweeting is False; hiding")
                return ()
        
        result = []
        responded = False
        if not skip_responses:
            direct, response = self.respond()
            if (direct or response):
                # a response to a direct message or mention was generated
                responded = True
                if direct:
                    result.append(direct.AsDict())
                if response:
                    result.append(response.AsDict())
                    
        if not responded:
            # no response was generated
            should_act = force_act or self.__selector.should_act()
            logging.debug("should_act: %s" % should_act)

            result.append(should_act)
            if not should_act:
                self.__reporter.did_not_act()
            else:
                # uses action parameter or selects one
                if not action: action = self.__selector.select_action()
                if action == ActionSelector.RETWEET:
                    # is there anything to retweet?
                    retweet, summary = self.retweet()
                    result.append(summary)
                elif action == ActionSelector.RANDOM_TWEET:
                    # no message; send random tweet
                    result.append(ActionSelector.RANDOM_TWEET)
                    status = self.mix()
                    result.append(status)
                else:
                    logging.debug("unexpected action '%s'" % action)
                    
        return tuple(result)
    

    def follow(self):
        self.__twitter.CreateFriendship()

    def message_master(self, message):
        self.__twitter.PostDirectMessage(cls.MASTER_USERNAME, message)

    def __direct_response(self, directs):
        direct = None
        
        for d in directs:
            logging.info("found direct message %s [%s %s] %s" % (d.id, d.created_at, d.sender_screen_name, d.text))
            response = TwitterResponseAccessor.get_by_message_id(str(d.id))
            if not response:
                direct = d
                break
            else:
                logging.debug("found response to direct message %s" % d.id)
        
        sent_message = None
        if direct:
            speaker = self.__select_speaker()
            sources, response_text = Mixer.new(speaker).mix_response(direct.text, min_results=1)
            logging.info("responding to direct message %s %s" % (direct.id, response_text))
            sent_message = self.__twitter.PostDirectMessage(direct.sender_screen_name, response_text)
            self.__reporter.posted(response_text)
            TwitterResponseAccessor.create(str(direct.id), response_id=str(sent_message.id), user=direct.sender_screen_name) 

        return sent_message
        
    def __public_response(self, messages):
        message = None
        
        for m in messages:
            logging.info("found public message: %s [%s %s] %s" % (m.id, m.created_at, m.user.screen_name, m.text))
            response = TwitterResponseAccessor.get_by_message_id(str(m.id))
            if not response:
                message = m
                break
            else:
                logging.debug("found response to public message %s" % m.id)
        
        sent_message = None
        if message:
            # TODO: search for username also
            username = message.user.screen_name
            parsed_tweet = parse_tweet(message.text)
            plain_tweet = parsed_tweet.plain_text
            speaker = self.__select_speaker()
            sources, mix = Mixer.new(speaker).mix_response(plain_tweet, min_results=1, max_length=130-len(username))
            response_text = "@%s %s" % (username, mix)
            logging.info("responding to public message %s: %s" % (message.id, response_text))
            
            sent_message = self.__twitter.PostUpdate(response_text, message.id)
            self.__reporter.posted(response_text)
            TwitterResponseAccessor.create(str(message.id), response_id=str(sent_message.id), user=username) 

        return sent_message


class TwitterWebActor:

    @classmethod
    def mix(cls, handler):
        helper = RequestHelper(handler)
        status = TwitterActor.mix()
        helper.write_json(status.AsDict())

    @classmethod
    def respond(cls, handler):
        helper = RequestHelper(handler)
        directs, publics = TwitterActor.respond()
        
        if not directs:
            directs = 0
        if not publics:
            publics = 0
            
        result = dict(directs=directs, publics=publics)
        helper.write_json(result)        

    @classmethod
    def act(cls, handler):
        helper = RequestHelper(handler)
        if handler.request.get("mock", False):
            actor = TwitterActor(twitter_api=MockTwitterApi())
        else:
            actor = TwitterActor()
            
        force_act = handler.request.get("force", False)
        action = handler.request.get("action")
        skip_responses = handler.request.get("skip_responses", False)
        act_response = actor.act(force_act=force_act, action=action, skip_responses=skip_responses)
        logging.debug("act_response: %s" % str(act_response))
        action = act_response[0]
        
        result = dict(action=action)
        if len(act_response) > 1:
            result['detailed_action'] = act_response[1]
        helper.write_json(result)
    
    
application = webapp.WSGIApplication(
    [('/api/twitter/act', TwitterActorHandler),
    ('/api/twitter/direct', TwitterDirectHandler),
    ('/api/twitter/mix', TwitterMixHandler),
    ('/api/twitter/followers', TwitterFollowersHandler),
    ('/api/twitter/friends', TwitterFriendsHandler),
    ('/api/twitter/friends/(.+)', TwitterFriendHandler),
    ('/api/twitter/friends-timeline', TwitterFriendsTimelineHandler),
    ('/api/twitter/respond', TwitterResponseHandler),
    ('/api/twitter/user/(.+)', TwitterUserHandler),],
    debug=True)

def main():
    basic_config()
    run_wsgi_app(application)

if __name__ == "__main__":
    main()