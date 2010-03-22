from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from katapult import log
from katapult.requests import RequestHelper

from antonym.accessors import ArtifactSourceAccessor, Counters
from antonym.core import NotFoundException
from antonym.model import ArtifactSource
from antonym.web.services import require_service_user


def source_hash(source):
    c = Counters.source_counter(source.name)
    return {'name': source.name, 'count': c.count()}
    
    
class SourcesHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self):
        helper = RequestHelper(self)
        results = []
        for s in ArtifactSource.all().fetch(100, 0):
            results.append(source_hash(s))
        helper.write_json(results)


class SourceHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self, name):
        helper = RequestHelper(self)
        source = ArtifactSource.get_by_name(name)
        if not source:
            helper.error(404)
            return
        helper.write_json(source_hash(source))
        
    @require_service_user()
    def delete(self, name):
        helper = RequestHelper(self)
        
        # delete source
        try:
            ArtifactSourceAccessor.delete(name)
            helper.set_status(204)
        except NotFoundException, ex:
            helper.error(404)
            return


application = webapp.WSGIApplication([
    ('/api/sources', SourcesHandler),
    ('/api/sources/(.+)', SourceHandler)
    ])


def main():
  log.config()
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
