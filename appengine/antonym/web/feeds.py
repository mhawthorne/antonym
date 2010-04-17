import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.ext import db

import simplejson as json

from katapult.core import Hashes

from katapult import log
from katapult.log import LoggerFactory
from katapult.models import get_reference_safely
from katapult.reflect import get_class
from katapult.requests import RequestHelper

from antonym.accessors import ArtifactSourceAccessor, UrlResourceAccessor
from antonym.core import NotFoundException
from antonym.model import Feed
from antonym.web import read_json_fields, unicode_hash
from antonym.web.services import require_service_user


def build_feed_hash(feed):
    source = get_reference_safely(feed, "artifact_source")
    return dict(url=feed.url,
        source=source.name if source else None,
        active=feed.active)


class FeedsHandler(webapp.RequestHandler):

    @require_service_user()
    def get(self):
        helper = RequestHelper(self)
        results = []
        for f in Feed.all().order('url').fetch(50):
            results.append(build_feed_hash(f))
        helper.write_json(results)


class FeedHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self, url):
        helper = RequestHelper(self)
        url = urllib.unquote(url)
        f = Feed.get_by_url(url, return_none=True)
        if not f:
            helper.error(404)
            return
        helper.write_json(build_feed_hash(f))

    @require_service_user()
    def put(self, url):
        logger = LoggerFactory.logger(self.__class__.__name__)
        helper = RequestHelper(self)
        
        url = urllib.unquote(url)
        success, values = read_json_fields(helper, "source", "active", logger=logger)
        if not success:
            return
        source_name, active = values
        
        # a Feed must be sole owner of an ArtifactSource;
        # fails if source already exists and is already linked to a feed
        source = ArtifactSourceAccessor.get_by_name(source_name, return_none=True)
        if source:
            source_feed_key = Feed.get_by_source(source, keys_only=True)
            if source_feed_key:
                msg = "source '%s' is referenced by feed %s" % (source_name, source_feed_key.name())
            helper.error(409, msg)
            return
        else:
            source = ArtifactSourceAccessor.create(source_name)
        
        # creates UrlResource if necessary
        resource = UrlResourceAccessor.get_by_url(url, return_none=True)
        if not resource:
            resource = UrlResourceAccessor.create(url)

        # create or update Feed
        feed = Feed.get_by_url(url, return_none=True)
        if feed:
            feed.artifact_source = source
            feed.url_resource = resource
            feed.put()
        else:
            Feed.create(url, artifact_source=source, url_resource=resource, active=bool(active))
        helper.set_status(204)

    @require_service_user()
    def delete(self, url):
        helper = RequestHelper(self)
        url = urllib.unquote(url)
        feed = Feed.get_by_url(url, return_none=True)
        if not feed:
            helper.error(404)
            return
        feed.delete()
        helper.set_status(204)


application = webapp.WSGIApplication(
    [('/api/feeds', FeedsHandler),
    ('/api/feeds/(.+)', FeedHandler)])


def main():
    log.config()
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
        
        