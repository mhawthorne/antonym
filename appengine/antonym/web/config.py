import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from katapult.models import entity_has_property, entity_to_hash
from katapult.requests import RequestHelper

from antonym.accessors import ConfigurationAccessor
from antonym.core import IllegalArgumentException
from antonym.web.services import require_service_user


class ConfigHandler(webapp.RequestHandler):

    @require_service_user()
    def get(self, key):
        helper = RequestHelper(self)
        config = ConfigurationAccessor.get()
        result = None
        if config:
            if key:
                if entity_has_property(config, key):
                    result = getattr(config, key)
                else:
                    helper.error(400, "invalid key")
                    return
            else:
                result = entity_to_hash(config)
        else:
            result = {}
        helper.write_json(result)

    @require_service_user()
    def put(self, key):
        helper = RequestHelper(self)
        if not self.request.body:
            helper.error(400, "body required")
            return
            
        value = self.request.body
        logging.info("%s=%s" % (key, value))
        try:
            ConfigurationAccessor.update(**{key: value})
        except IllegalArgumentException, e:
            helper.error(400, "invalid key")
            return
        helper.set_status(204)

    @require_service_user()
    def delete(self, key):
        helper = RequestHelper(self)
        ConfigurationAccessor.update(key=None)
        helper.set_status(204)


application = webapp.WSGIApplication([
    ('/api/config/?([^/]+)?', ConfigHandler)])


def main():
    logging.basicConfig(level=logging.DEBUG)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()