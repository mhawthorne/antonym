import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from katapult.log import basic_config
from katapult.reflect import create_decorated_class, decorate_class
from katapult.security import forbidden

from antonym.web.activity import ActivityLogHandler
from antonym.web.artifacts import ArtifactHandler, ArtifactsHandler
from antonym.web.feeds import FeedHandler, FeedsHandler
from antonym.web.ingest import IngestHandler, IngestParseHandler
from antonym.web.mixtures import MixtureHandler, MixtureResponseHandler
from antonym.web.services import require_digest_login, require_service_user
from antonym.web.sources import SourceCleanerHandler, SourceHandler, SourcesHandler


ALLOW_PUBLIC_WRITES = "allow_public_writes"

public_prefix = "/api/public"
private_prefix = "/api/private"

allow_public_writes = { ALLOW_PUBLIC_WRITES: True }

def build_path_list():
    # TODO: need to order paths
    # keys are url regexes, values are (handler class, handler info dict) tuples
    service_paths = (
        ("activity", ActivityLogHandler, {}),
        ("artifacts", ArtifactsHandler, allow_public_writes),
        ("artifacts/(.+)", ArtifactHandler, allow_public_writes),
        ("feeds", FeedsHandler, {}),
        ("feeds/(.+)", FeedHandler, {}),
        ("ingest/(.+)", IngestHandler, {}),
        ("ingest-parse/(.+)", IngestParseHandler, {}),
        ("mixtures(?:/(.+))?", MixtureHandler, {}),
        ("sources/-/clean", SourceCleanerHandler, {}),
        ("sources/(.+)", SourceHandler, allow_public_writes),
        ("sources", SourcesHandler, {})
    )

    read_methods = ("head", "get")
    write_methods = ("delete", "post", "put")
    all_methods = read_methods + write_methods

    google_decorator = require_service_user()
    digest_decorator = require_digest_login()
    forbidden_decorator = forbidden()

    path_list = []
    for path, klass, info in service_paths:
        pretty_svc = "%s -> %s" % (path, klass.__name__)
        # logging.debug("%s %s" % (pretty_svc, info))
    
        # all actions accessable by google service user
        path_list.append(("%s/%s" % (private_prefix, path), create_decorated_class(klass, google_decorator, methods=all_methods)))
    
        logging.debug("%s %s %s" % (info, ALLOW_PUBLIC_WRITES, info.get(ALLOW_PUBLIC_WRITES)))
    
        if info.get(ALLOW_PUBLIC_WRITES):
            logging.debug("enabling public read-write access for %s" % pretty_svc)
            # enables digest for read methods
            public_klass = create_decorated_class(klass, digest_decorator, methods=all_methods)            
        else:
            logging.debug("enabling public read-only access for %s" % pretty_svc)
        
            # enables digest for read methods
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
