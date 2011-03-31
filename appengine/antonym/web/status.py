import logging
import sys

from google.appengine.ext import webapp

from katapult.reflect import get_full_class_name
from katapult.requests import RequestHelper

from antonym.ttwitter import TwitterConnector


class StatusHandler(webapp.RequestHandler):
    
    def get(self):
        helper = RequestHelper(self)
        result = dict(twitter_api=get_full_class_name(TwitterConnector.new_api()))
        result["sys.getdefaultencoding"] = sys.getdefaultencoding()
        helper.write_json(result)