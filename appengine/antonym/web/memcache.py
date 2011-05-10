from google.appengine.api import memcache
from google.appengine.ext.webapp import RequestHandler

from katapult.requests import RequestHelper


class MemcacheHandler(RequestHandler):
    
    def get(self):
        helper = RequestHelper(self)
        helper.write_json(memcache.get_stats())
        
    def delete(self):
        helper = RequestHelper(self)
        memcache.flush_all()
        helper.set_status(204)
