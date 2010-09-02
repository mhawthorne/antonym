from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from katapult.requests import RequestHelper

# hack attempt to make a deferred task finish

class SuccessHandler(webapp.RequestHandler):
    
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
        helper.write_json({'msg': 'hack success'})

application = webapp.WSGIApplication([('/.*', SuccessHandler)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()