from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from antonym.web.tweeter import TwitterActor

from katapult.log import config as logging_config, LoggerFactory
from katapult.requests import RequestHelper


class CronTwitterMixHandler(webapp.RequestHandler):
    
    def get(self):
        helper = RequestHelper(self)
        test = self.request.get("test")
        if test:
            helper.write_json(dict(test="win"))
        else:
            TwitterActor.mix(self)


class CronActorHandler(webapp.RequestHandler):

    def get(self):
        # choose action
        
        # default: find responses
        TwitterActor.response(self)

application = webapp.WSGIApplication(
    [('/cron/actor', CronActorHandler),
    ('/cron/twitter/mix', CronTwitterMixHandler)],
    debug=True)

def main():
    logging_config()
    run_wsgi_app(application)

if __name__ == "__main__":
    main()