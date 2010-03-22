import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import simplejson as json

from antonym.accessors import MixtureAccessor
from antonym.core import DataException
from antonym.web.services import require_service_user

from katapult.auth import require_admin
from katapult.core import Dates, Hashes
from katapult.log import config as log_config, LoggerFactory
from katapult.models import Models
from katapult.requests import time_request, RequestHelper


class MixtureHandler(webapp.RequestHandler):
    
    @require_service_user()
    @time_request()
    def get(self, source_name):
        helper = RequestHelper(self)
        logger = LoggerFactory.logger(self.__class__.__name__)
        try:
            logger.debug("source_name: %s" % source_name)
            source, content = MixtureAccessor.mix(source_name=source_name)
            sources = [source.name]
            mix_hash = {'sources': sources, 'body': content}
            helper.write_json(mix_hash)
        except DataException, ex:
            helper.error(503, "no content found")


application = webapp.WSGIApplication(
  [('/api/mixture/?(.+)?', MixtureHandler)],
  debug=True)


def main():
  log_config()
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
