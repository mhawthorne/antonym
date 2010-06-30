import logging
import random
import time

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from katapult.log import basic_config
from katapult.requests import RequestHelper

# hack attempt to make a deferred task finish

class DebugHandler(webapp.RequestHandler):
    
    def get(self):
        self.__default()
        
    def post(self):
        self.__default()
        
    def put(self):
        self.__default()
        
    def delete(self):
        self.__default()

    def head(self):
        self.__default()

    def __default(self):
        helper = RequestHelper(self)
        m = self.request.method
        if m in ("DELETE", "PUT"):
            sleep = random.randint(0, 10) / 2
            logging.debug("sleeping for %ds" % sleep)
            time.sleep(sleep)
        elif m == "GET":
            helper.write_json({'msg': 'hack success'})
        else:
            pass

application = webapp.WSGIApplication([('/.*', DebugHandler)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    basic_config()
    main()