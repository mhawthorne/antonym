import re

from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from katapult import log
from katapult.requests import RequestHelper

from antonym.accessors import ArtifactSourceAccessor, Counters, UrlResourceAccessor
from antonym.core import NotFoundException
from antonym.model import UrlResource
from antonym.web.services import require_service_user


def resource_hash(resource):
    h = { "url": resource.url,
        "etag": resource.etag,
        "modified": resource.modified.isoformat() }
        
    if resource.source_modified:
        h["source-modified"] = resource.source_modified.isoformat()
        
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


class ResourcesSearchHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self):
        helper = RequestHelper(self)
        search_results = self.__search(helper)
        if search_results is not None:
            helper.write_json([resource_hash(u) for u in search_results])

    @require_service_user()
    def delete(self):
        helper = RequestHelper(self)
        search_results = self.__search(helper)
        if search_results:
            keys = [u.key() for u in search_results]
            db.delete(keys)
            helper.write_json([k.name() for k in keys])
        else:
            helper.set_status(204)

    def __search(self, helper):
        q = self.request.get("q")
        if not q:
            helper.error(400, "q must be provided")
            return

        regex = re.compile(q)
        return UrlResource.search_by_url(regex)


class ResourceHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self, url):
        helper = RequestHelper(self)
        resource = UrlResource.get_by_url(url, return_none=True)
        if not resource:
            helper.error(404)
            return
        helper.write_json(resource_hash(resource))


# application = webapp.WSGIApplication([
#     ('/api/resources/-/search', ResourcesSearchHandler),
#     ('/api/resources/?(\d+)?', ResourcesHandler),
#     ('/api/resources/(.+)', ResourceHandler)
#     ])
# 
# 
# def main():
#   log.config()
#   run_wsgi_app(application)
# 
# if __name__ == "__main__":
#   main()