from datetime import datetime
import logging

from google.appengine.ext import webapp

from katapult.caching import MemcacheQueue
from katapult.dates import timestamp
from katapult.requests import RequestHelper

from antonym.queues import get_activity_queue


class ActivityReporter(object):

    def __init__(self):
        self.__queue = get_activity_queue()

    def did_not_act(self):
        self.__event(choice="did not act")

    def posted(self, msg):
        self.__event(posted=msg)

    def retweeted(self, msg):
        self.__event(retweeted=msg)
        
    def __event(self, **kw):
        kw["timestamp"] = datetime.now().isoformat()
        self.__queue.add(kw)


class ActivityLogHandler(webapp.RequestHandler):

    def get(self, **kw):
        helper = RequestHelper(self)
        
        # read actions from queue; return as json
        q = get_activity_queue()
        items = q.items()
        
        helper.write_json(items)