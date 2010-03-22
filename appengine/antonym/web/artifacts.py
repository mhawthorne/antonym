import urllib

from google.appengine.api import users
from google.appengine.api.users import User
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import simplejson as json

from antonym.accessors import ArtifactAccessor
from antonym.core import DuplicateDataException, NotFoundException
from antonym.model import ArtifactInfo, ArtifactContent
from antonym.web.services import require_biggie_user, require_digest_login, require_service_user

from katapult.core import Dates, Hashes
from katapult.log import config as log_config, LoggerFactory
from katapult.models import Models
from katapult.requests import RequestHelper


class ArtifactsHelper:
    
    API_PREFIX = "/api/artifacts"
    
    API_PREFIX_2 = "/api/artifacts2"
    
    @classmethod
    def post(cls, request_handler, **kw):
        logger = LoggerFactory.logger(request_handler.__class__.__name__)
        helper = RequestHelper(request_handler)
        request = request_handler.request
        username = kw.get("username", None)
        user = User(username) if username else users.get_current_user()
        
        json_body = request.body
        if not json_body:
            helper.error(400, "body required")
            return
            
        decoded_body = urllib.unquote(json_body)
        try:
            artifact_hash = json.loads(decoded_body)
        except json.JSONDecodeError, e:
            msg = "malformed json: %s" % decoded_body
            helper.error(400, msg)
            logger.info(msg)
            return
        
        # de-unicodes keys
        decoded_hash = {}
        for k, v in artifact_hash.iteritems():
            decoded_hash[k.encode("utf-8")] = v
        
        fields = ("source", "content-type", "body")
        result = Hashes.fetch_fields(decoded_hash, fields)
        if result.missing_fields:
            msg = "missing fields: %s" % result.missing_fields
            helper.error(400, msg)
            logger.info(msg)
            return
        source, content_type, content_body = result.values
        
        # name of info_key is guid
        try:
            info_key, src_key, content_key = ArtifactAccessor.save(source=source,
                content_type=content_type,
                body=content_body,
                modified_by=user)
            guid = info_key.name()
            helper.set_status(204)
            location = ArtifactsHandler.artifact_uri(request, guid)
            helper.header("Location", location)
        except DuplicateDataException, ex:
            helper.error(409, ex.message)

    @classmethod
    def get(cls, rhandler, guid, **kw):
        helper = RequestHelper(rhandler)
        
        artifact_info = ArtifactInfo.get_by_guid(guid)
        artifact_content = ArtifactContent.get_by_guid(guid)
        if artifact_info and artifact_content:
            artifact_hash = ArtifactsHelper.artifact_to_hash(artifact_info, artifact_content)
            helper.write_json(artifact_hash)
        else:
            helper.error(404)

    @classmethod
    def delete(cls, rhandler, guid, **kw):
        helper = RequestHelper(rhandler)
        try:
            ArtifactAccessor.delete(guid)
            helper.set_status(204)
        except NotFoundException, ex:
            helper.error(404)

    @classmethod
    def put(cls, rhandler, guid, **kw):
        l = cls._logger()
        helper = RequestHelper(rhandler)
        
        artifact = ArtifactInfo.get_by_guid(guid)
        if not artifact:
            helper.error(404)
            return
            
        # removes existing properties
        props = ArtifactInfo.properties().keys()
        for prop in props:
            delattr(artifact, prop)
        
        # save artifact
        ArtifactInfo.save(artifact)

    @classmethod
    def artifact_to_hash(cls, artifact_info, artifact_content):
        artifact_hash = {'guid': artifact_info.guid,
            'source': artifact_info.source.name,
            'content-type': artifact_info.content_type,
            'modified': Dates.format(artifact_info.modified),
            'modified-by': artifact_info.modified_by.email(),
            'body': artifact_content.body }
        return artifact_hash
        
    @classmethod
    def _logger(cls):
        return LoggerFactory.logger(cls.__name__)


class ArtifactsHandler(webapp.RequestHandler):
    
    @classmethod
    def artifact_uri(cls, request, guid):
        #return "http://%s%s/%s" % (request.environ['HTTP_HOST'], ArtifactsHelper.API_PREFIX, guid)
        return "%s%s/%s" % (request.host_url, request.path, guid)
    
    @require_service_user()  
    def post(self):
        ArtifactsHelper.post(self)

    
class BulkArtifactsHandler(webapp.RequestHandler):
    
    @require_digest_login()
    def post(self, **kw):
        ArtifactsHelper.post(self, **kw)


class ArtifactHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self, guid):
        ArtifactsHelper.get(self, guid)
        
    @require_service_user()
    def delete(self, guid):
        ArtifactsHelper.delete(self, guid)
        
    @require_service_user()
    def put(self, guid):
        ArtifactsHandler.put(self, guid)


class BulkArtifactHandler(webapp.RequestHandler):
    
    @require_digest_login()
    def get(self, guid, **kw):
        ArtifactsHelper.get(self, guid, **kw)
        
    @require_digest_login()
    def delete(self, guid, **kw):
        ArtifactsHelper.delete(self, guid, **kw)
        
    @require_digest_login()
    def put(self, guid, **kw):
        ArtifactsHandler.put(self, guid, **kw)


class ArtifactSearchHandler(webapp.RequestHandler):
    
    @require_service_user()
    def get(self):
        helper = RequestHelper(self)
        q = self.request.get("q", None)
        if not q:
            helper.error(400, "q not provided.")
            return
            
        q_results = ArtifactContent.all().search(q)
        json_results = []
        if q_results.count():
            for content in q_results.fetch(100):
                info = ArtifactInfo.get_by_guid(content.guid)
                json_results.append(ArtifactsHelper.artifact_to_hash(info, content))
        helper.write_json(json_results)


application = webapp.WSGIApplication(
  [('%s/-/search.*' % ArtifactsHelper.API_PREFIX, ArtifactSearchHandler),
  (ArtifactsHelper.API_PREFIX, ArtifactsHandler),
  ('%s/(.+)' % ArtifactsHelper.API_PREFIX, ArtifactHandler),
   (ArtifactsHelper.API_PREFIX_2, BulkArtifactsHandler),
   ('%s/(.+)' % ArtifactsHelper.API_PREFIX_2, BulkArtifactHandler)],
  debug=True)


def main():
  log_config()
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
