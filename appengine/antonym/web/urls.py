import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from katapult.log import basic_config
from katapult.reflect import create_decorated_class, decorate_class
from katapult.security import forbidden

from antonym.web.activity import ActivityLogHandler
from antonym.web.artifacts import ArtifactBulkDeleteHandler, ArtifactHandler, ArtifactsHandler, ArtifactsSearchHandler
from antonym.web.config import ConfigHandler
from antonym.web.feeds import FeedHandler, FeedsHandler
from antonym.web.ingest import IngestHandler, IngestParseHandler
from antonym.web.memcache import MemcacheHandler
from antonym.web.mixtures import MixtureHandler, MixtureResponseHandler
from antonym.web.resources import ResourcesSearchHandler, ResourcesHandler, ResourceHandler
from antonym.web.responses import ResponsesHandler
from antonym.web.services import require_digest_login, require_service_user
from antonym.web.sources import SourceCleanerHandler, SourceHandler, SourcesHandler
from antonym.web.stats import StatsHandler
from antonym.web.status import StatusHandler
from antonym.web.tweeter import TwitterActorHandler, TwitterApiHandler, TwitterDirectHandler, TwitterMixHandler,\
    TwitterFollowersHandler, TwitterFriendsHandler, TwitterFriendHandler, TwitterMentionsHandler,\
    TwitterFriendsTimelineHandler, TwitterPublicTimelineHandler, TwitterResponseHandler, TwitterUserHandler

ALLOW_PUBLIC_WRITES = "allow_public_writes"
ALLOW_OPEN_READS = "allow_public_reads"

public_prefix = "/api/public"
private_prefix = "/api/private"

allow_public_writes = { ALLOW_PUBLIC_WRITES: True }
allow_open_reads = { ALLOW_OPEN_READS: True }


def build_path_list():
    # TODO: need to order paths
    # keys are url regexes, values are (handler class, handler info dict) tuples
    service_paths = (
        ("activity", ActivityLogHandler, None),
        ("artifacts", ArtifactsHandler, allow_public_writes),
        ("artifacts/-/search", ArtifactsSearchHandler, None),
        ("artifacts/-/delete", ArtifactBulkDeleteHandler, None),
        ("artifacts/(.+)", ArtifactHandler, allow_public_writes),
        ('config/?([^/]+)?', ConfigHandler, None),
        ("feeds", FeedsHandler, None),
        ("feeds/(.+)", FeedHandler, None),
        ("ingest/(.+)", IngestHandler, None),
        ("ingest-parse/(.+)", IngestParseHandler, None),
        ("memcache", MemcacheHandler),
        ("mixtures(?:/(.+))?", MixtureHandler, allow_open_reads),
        ('resources/-/search', ResourcesSearchHandler),
        ('resources/?(\d+)?', ResourcesHandler),
        ('resources/(.+)', ResourceHandler),
        ('responses', ResponsesHandler),
        ("sources/-/clean", SourceCleanerHandler, None),
        ("sources/(.+)", SourceHandler, allow_public_writes),
        ("sources", SourcesHandler, None),
		("stats", StatsHandler, None),
        ("status", StatusHandler, None),
        ('twitter/act', TwitterActorHandler, None),
        ('twitter/direct', TwitterDirectHandler, None),
        ('twitter/mix', TwitterMixHandler, None),
        ('twitter/followers', TwitterFollowersHandler, None),
        ('twitter/friends', TwitterFriendsHandler, None),
        ('twitter/friends/(.+)', TwitterFriendHandler, None),
        ('twitter/friends-timeline', TwitterFriendsTimelineHandler),
        ('twitter/mentions/(\d+)', TwitterMentionsHandler),
        ('twitter/public-timeline', TwitterPublicTimelineHandler),
        ('twitter/raw/(.+)', TwitterApiHandler),
        ('twitter/respond', TwitterResponseHandler),
        ('twitter/user/(.+)', TwitterUserHandler)
    )

    read_methods = ("head", "get")
    write_methods = ("delete", "post", "put")
    all_methods = read_methods + write_methods

    google_decorator = require_service_user()
    digest_decorator = require_digest_login()
    forbidden_decorator = forbidden()

    path_list = []
    for parts in service_paths:
        if len(parts) == 3:
            path, klass, info = parts
        elif len(parts) == 2:
            path, klass = parts
        else:
            logging.warn("invalid tuple: %s" % str(parts)) 
            continue
            
        pretty_svc = "%s -> %s" % (path, klass.__name__)
    
        # all actions accessable by google service user
        path_list.append(("%s/%s" % (private_prefix, path), create_decorated_class(klass, google_decorator, methods=all_methods)))
    
        if info:
            public_klass = klass
            
            if info.get(ALLOW_PUBLIC_WRITES):
                # wraps all methods with digest.
                logging.debug("enabling public read-write access for %s" % pretty_svc)
                public_klass = create_decorated_class(klass, digest_decorator, methods=all_methods)
                
            if info.get(ALLOW_OPEN_READS):
                # wraps write methods with digest.  leaves reads methods unsecured.
                logging.debug("enabling open read access for %s" % pretty_svc)
                public_klass = create_decorated_class(klass, digest_decorator, methods=write_methods)                
        else:
            logging.debug("enabling public read-only access for %s" % pretty_svc)
        
            # wraps read methods with digest
            public_klass = create_decorated_class(klass, digest_decorator, methods=read_methods)
            
            # rejects digest write methods
            decorate_class(public_klass, forbidden_decorator, methods=write_methods)
    
        path_list.append(("%s/%s" % (public_prefix, path), public_klass))

    return path_list


path_list = build_path_list()


def main():
    basic_config()
    application = webapp.WSGIApplication(path_list)
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
