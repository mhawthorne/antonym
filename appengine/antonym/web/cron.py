import logging
import random
import re
import traceback

from google.appengine.api.labs import taskqueue
from google.appengine.ext import deferred
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from antonym.accessors import ConfigurationAccessor
from antonym.model import Feed
from antonym.web.ingest import IngestWebActor
from antonym.web.tweeter import TwitterActor

from katapult import dates
from katapult.core import Exceptions
from katapult.log import basic_config
from katapult.requests import monitor_request, RequestHelper


def set_error_status(helper):
    helper.set_status(205)


class CronTwitterActorHandler(webapp.RequestHandler):

    # in most frequent case, tweets will be 10 minutes apart
    _minutes = xrange(5, 25)

    def get(self):
        helper = RequestHelper(self)
        
        # calculates random number of minutes
        minute = random.choice(self._minutes)
        
        taskqueue.add(url=SafeTwitterActorHandler.PATH, countdown=minute * 60)
        msg = 'scheduled %d minutes in the future' % minute
        logging.debug(msg)
        helper.write_json({'msg': msg})


class SafeTwitterActorHandler(webapp.RequestHandler):
    
    PATH = '/cron/twitter/act-safe'
    
    def post(self):
        result = None
        try:
            result = TwitterActor().act()
        except Exception, e:
            msg = Exceptions.format_last()
            logging.error(msg)
            result = (e, msg)
            set_error_status(RequestHelper(self))
        logging.info("result: %s" % result)
        return result


class CronIngestDriverHandler(webapp.RequestHandler):
    
    _source_sanitize_regex = re.compile("[^\w-]+")
    
    def get(self):
        """ enqueues all active Feeds for ingest """
        # find all active feeds
        q = Feed.find_active()
        if not q.count():
            logging.warn("no active feeds found")
            return
        
        # generates unique is for task names
        ingest_id = dates.timestamp(separator="")
        
        for f in q.fetch(1000):
            try:
                # schedule tasks to ingest by source name
                source_name = f.artifact_source.name
                
                # replace invalid chars from source name
                normalized_source_name = self._source_sanitize_regex.sub("-", source_name)
                task_name = "ingest-%s-%s" % (normalized_source_name, ingest_id)
                taskqueue.add(name=task_name, url="/cron/ingest/%s" % source_name)
                logging.debug("queued ingest task %s for source '%s' (feed %s)" % (task_name, source_name, f.url))
            except (taskqueue.TaskAlreadyExistsError, taskqueue.TombstonedTaskError):
                logging.warn(traceback.format_exc())


class CronIngestHandler(webapp.RequestHandler):

    @monitor_request(always_succeed=True)
    def post(self, source_name):
        IngestWebActor.ingest(self, source_name)


application = webapp.WSGIApplication(
    [('/cron/twitter/act', CronTwitterActorHandler),
    (SafeTwitterActorHandler.PATH, SafeTwitterActorHandler),
    ('/cron/ingest', CronIngestDriverHandler),
    ('/cron/ingest/(.+)', CronIngestHandler)],
    debug=True)

def main():
    basic_config()
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()