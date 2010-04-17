from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from katapult import log
from katapult.requests import RequestHelper

from antonym.accessors import ArtifactSourceAccessor, Counters
from antonym.core import NotFoundException
from antonym.model import UrlResource
from antonym.web.services import require_service_user


def resource_hash(resource):
    h = { "url": resource.url,
        "etag": resource.etag,
        "modified": resource.modified.isoformat() }
        
    if resource.source_modified:
        h["source-modified"] = resource.source_modified.isoformat()
        
    # artifacts = []
    # for a in resource.artifactinfo_set:
    #     artifacts.append(dict(guid=a.guid))
    # if artifacts:
    #     h["artifacts"] = artifacts
    return h


class ResourcesHandler(webapp.RequestHandler):
    
    BATCH_SIZE = 20
    
    @require_service_user()
    def get(self, page):
        page = int(page) if page else 0
        
        helper = RequestHelper(self)
        results = []
        for u in UrlResource.all().fetch(self.BATCH_SIZE, page * self.BATCH_SIZE):
            results.append(resource_hash(u))
        helper.write_json(results)


class ResourceHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self, url):
        helper = RequestHelper(self)
        resource = UrlResource.get_by_url(url, return_none=True)
        if not resource:
            helper.error(404)
            return
        helper.write_json(resource_hash(resource))


application = webapp.WSGIApplication([
    ('/api/resources/?(\d+)?', ResourcesHandler),
    ('/api/resources/(.+)', ResourceHandler)
    ])


def main():
  log.config()
  run_wsgi_app(application)

if __name__ == "__main__":
  main()