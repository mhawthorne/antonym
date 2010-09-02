from datetime import datetime
import logging
import urllib

from google.appengine.api import users
from google.appengine.api.users import User
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.ext import db

import simplejson as json

from katapult.core import Hashes

from katapult import log
from katapult.core import Exceptions

from katapult.reflect import get_class
from katapult.requests import RequestHelper

from antonym.accessors import ArtifactAccessor, ArtifactSourceAccessor, UrlResourceAccessor
from antonym.core import AppException, NotFoundException
from antonym.ingest import model
from antonym.model import Feed
from antonym.web import read_json_fields, unicode_hash
from antonym.web.services import require_service_user, Services


class IngestWebActor:
    
    @classmethod
    def ingest(cls, handler, source_name):
        helper = RequestHelper(handler)
        source_name = urllib.unquote(source_name)
    
        # TODO: get from cache
        f = Feed.get_by_source_name(source_name, return_none=True)
        if not f:
            helper.error(404)
            return
    
        results = []
    
        # TODO: use etag from previous ingest
        error_call = lambda entry, ex: logging.error(Exceptions.format_last())
    
        user = users.get_current_user()
        if not user:
            # there is no logged in user for cron requests
            user = User(Services.API_USER)
            
        for artifact_guid, entry, created in model.ingest_feed_entries(f, user, error_call=error_call):
            results.append({ "artifact-guid": artifact_guid,
                "url": entry.link,
                "title": entry.title,
                "created": created })
            
        helper.write_json(results)


class IngestHandler(webapp.RequestHandler):
    
    @require_service_user()
    def post(self, source_name):
        IngestWebActor.ingest(self, source_name)


class IngestParseHandler(webapp.RequestHandler):

    @require_service_user()
    def get(self, feed_url):
        feed_url = "http://%s" % feed_url
        helper = RequestHelper(self)
        entries = [dict(title=e.title, link=e.link, content=e.stripped_content, modified=str(e.modified)) for e in model.parse_feed_entries(feed_url)]
        helper.write_json(entries)


# application = webapp.WSGIApplication([('/api/ingest/(.+)', IngestHandler)])
# 
# def main():
#     log.config()
#     run_wsgi_app(application)
# 
# if __name__ == "__main__":
#     main()