from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.ext import db

import simplejson as json

from katapult import log
from katapult.reflect import get_class
from katapult.requests import RequestHelper

from antonym.web.services import require_service_user


class StatsHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self):
        helper = RequestHelper(self)
        results = []
        for s in db.stats.KindStat.all():
            results.append({'kind': s.kind_name,
                'count': s.count,
                'bytes': s.bytes})
        helper.write_json(results)


class KindHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self, kind):
        self.__send_count(self.__find_kind_keys(kind))
    
    @require_service_user()
    def delete(self, kind):
        keys = self.__find_kind_keys(kind)
        db.delete(keys)
        self.__send_count(keys)
    
    def __send_count(self, keys):
        helper = RequestHelper(self)
        count = len(keys)
        result = {'count': count}
        helper.write_json(result)        
        
    def __find_kind_keys(self, kind):
        klass = get_class('antonym.model.%s' % kind)
        results = []
        # TODO: couldn't use keys_only=True here since SearchableModel.all() doesn't support it
        for k in klass.all():
            results.append(k)
        return results
        
        
application = webapp.WSGIApplication(
    [('/api/da/kinds/(.+)', KindHandler),
    ('/api/da/stats', StatsHandler)])

def main():
    log.config()
    run_wsgi_app(application)

if __name__ == "__main__":
    main()