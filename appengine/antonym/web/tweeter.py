import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import simplejson as json
import twitter

from antonym.accessors import MixtureAccessor
from antonym.web.services import require_service_user
from antonym.web import service_users

from katapult.log import config as logging_config
from katapult.requests import RequestHelper


class TwitterConnector:
    
    @classmethod
    def new_api(cls):
        # TODO: use memcache?
        u, p = service_users.twitter_default_creds()
        return twitter.Api(username=u, password=p, cache=None)


class TwitterStateHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self):
        helper = RequestHelper(self)
        t_api = TwitterConnector.new_api()
        def user_hash(user):
            return {'name': user.name, 
                'screen-name': user.screen_name, 
                'url': user.url,
                'statuses-count': user.statuses_count,
                'followers-count': user.followers_count,
                'friends-count': user.friends_count }
        friends = [user_hash(u) for u in t_api.GetFriends()]
        followers = sorted([user_hash(u) for u in t_api.GetFollowers()], key=lambda u: u['screen-name'])
        result = dict(friends=friends, followers=followers)
        helper.write_json(result)


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
        TwitterActor.respond(self)


class TwitterActor:
    
    @classmethod
    def mix(cls, handler):
        helper = RequestHelper(handler)
        
        source, content = MixtureAccessor.mix()
        t_api = TwitterConnector.new_api()
        status = t_api.PostUpdate(content)
        helper.write_json(status.AsDict())

    @classmethod
    def respond(cls, handler):
        helper = RequestHelper(handler)
        t_api = TwitterConnector.new_api()
        statuses = [s.AsDict() for s in t_api.GetReplies()]
        helper.write_json(statuses)        


application = webapp.WSGIApplication(
    [('/api/twitter/act', TwitterActorHandler),
    ('/api/twitter/direct', TwitterDirectHandler),
    ('/api/twitter/mix', TwitterMixHandler),
    ('/api/twitter/state', TwitterStateHandler)],
    debug=True)

def main():
    logging_config()
    run_wsgi_app(application)

if __name__ == "__main__":
    main()