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

from antonym import rrandom
from antonym.accessors import ConfigurationAccessor, TwitterResponseAccessor
from antonym.core import AppException, IllegalStateException
from antonym.ttwitter import describe_status, sorted_user_list, user_hash, ActionSelector, ReadOnlyTwitterApi, TwitterActor, TwitterConnector
from antonym.web.activity import ActivityReporter
from antonym.web.services import require_service_user
from antonym.web import service_users

from katapult.core import Record
from katapult.log import basic_config
from katapult.requests import RequestHelper


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
        TwitterWebActor.mix(self)


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
        c = self.request.get("c", 20)
        helper = RequestHelper(self)
        t_api = TwitterConnector.new_api()
        statuses = [describe_status(s) for s in t_api.GetFriendsTimeline(count=c)]
        helper.write_json(statuses)


class TwitterPublicTimelineHandler(webapp.RequestHandler):
  
    @require_service_user()
    def get(self):
        c = self.request.get("c", 20)
        helper = RequestHelper(self)
        t_api = TwitterConnector.new_api()
        statuses = [describe_status(s) for s in t_api.GetPublicTimeline()]
        helper.write_json(statuses)


class TwitterMentionsHandler(webapp.RequestHandler):
  
    @require_service_user()
    def get(self, page):
        helper = RequestHelper(self)
        page = int(page)
        t_api = TwitterConnector.new_api()
        raw_mentions = t_api.GetReplies(page=page)
        pretty_mentions = []
        for m in raw_mentions:
            d = dict(id=m.id, 
                created=m.created_at,
                user=m.user.screen_name,
                text=m.text)
            pretty_mentions.append(d)
        helper.write_json(pretty_mentions)


class TwitterApiHandler(webapp.RequestHandler):
  
    @require_service_user()
    def get(self, path):
        helper = RequestHelper(self)
        t_api = TwitterConnector.new_api()
        body = t_api.FetchPath("%s.json" % path)
        try:
            helper.write_json(json.loads(body))
        except json.JSONDecodeError, e:
            helper.write(body)
        


class TwitterWebActor:

    @classmethod
    def mix(cls, handler):
        helper = RequestHelper(handler)
        status = TwitterActor().mix()
        helper.write_json(status.AsDict())

    @classmethod
    def respond(cls, handler):
        helper = RequestHelper(handler)
        directs, publics = TwitterActor().respond()
        
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
            result['detailed_action'] = act_response
        helper.write_json(result)
