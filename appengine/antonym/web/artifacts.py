import logging
import urllib

from google.appengine.api import users
from google.appengine.api.users import User
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import simplejson as json

from antonym.accessors import ArtifactAccessor
from antonym.core import DuplicateDataException, NotFoundException
from antonym.model import ArtifactInfo, ArtifactContent

from katapult.core import Hashes
from katapult import dates, log
from katapult.models import Models
from katapult.requests import RequestHelper


class ArtifactsHelper:
        
    @classmethod
    def post(cls, request_handler, **kw):
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
            logging.info(msg)
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
            logging.info(msg)
            return
        source, content_type, content_body = result.values
        
        # name of info_key is guid
        try:
            info_key, src_key, content_key = ArtifactAccessor.create(source=source,
                content_type=content_type,
                body=content_body,
                modified_by=user)
            guid = info_key.name()
            helper.set_status(204)
            location = cls.artifact_uri(request, guid)
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
        # in theory neither info or content should be None,
        # but I'm dealing with a bug where infos were deleted for a source,
        # but content was not
        
        artifact_hash = {}
        
        if artifact_info is not None:
          artifact_hash['guid'] = artifact_info.guid
          artifact_hash['source'] = artifact_info.source_name
          artifact_hash['content-type'] = artifact_info.content_type
          artifact_hash['modified'] = artifact_info.modified.isoformat()
          artifact_hash['modified-by'] = artifact_info.modified_by.email()
          
          if artifact_info.url:
            artifact_hash["url"] = artifact_info.url
            
        if artifact_content is not None:
          artifact_hash['guid'] = artifact_content.guid
          artifact_hash['source'] = artifact_content.source_name
          artifact_hash['body'] = artifact_content.body
          artifact_hash['modified'] = artifact_content.modified.isoformat()
          
        return artifact_hash

    @classmethod
    def artifact_uri(cls, request, guid, **kw):
        return "%s%s/%s" % (request.host_url, request.path, guid)


class ArtifactsHandler(webapp.RequestHandler):
    
    def post(self, **kw):
        ArtifactsHelper.post(self, **kw)

    def get(self, **kw):
        helper = RequestHelper(self)
        start = int(self.request.get("start", 0))
        count = int(self.request.get("count", 10))
        
        q = ArtifactInfo.all().order("-modified")
        json_results = []
        if q.count():
            for a_info in q.fetch(count, start):
                a_content = ArtifactAccessor.get_content_by_guid(a_info.guid)
                json_results.append(ArtifactsHelper.artifact_to_hash(a_info, a_content))
        helper.write_json(json_results)


class ArtifactBulkDeleteHandler(webapp.RequestHandler):
    """ I wanted this to be in the DELETE method for ArtifactsHandler, but a client limitation currently prevents it """
    
    def post(self):
        helper = RequestHelper(self)
        
        json_body = self.request.body
        if not json_body:
            helper.error(400, "body required")
            return
            
        decoded_body = urllib.unquote(json_body)
        try:
            body_hash = json.loads(decoded_body)
        except json.JSONDecodeError, e:
            msg = "malformed json: %s" % decoded_body
            helper.error(400, msg)
            logging.info(msg)
            return
        
        ids = body_hash.get("ids", None)
        if not ids:
            msg = "no 'ids' field provided in JSON"
            helper.error(400, msg)
            logging.info(msg)
            return

        logging.info("deleting %s artifact(s)" % len(ids))

        contents = [c for c in ArtifactContent.get_by_key_name(ids) if c is not None]
        logging.info("deleting %s ArtifactContent instances" % len(contents))
        db.delete(contents)
            
        infos = [i for i in ArtifactInfo.get_by_key_name(ids) if i is not None]
        logging.info("deleting %s ArtifactInfo instances" % len(infos))
        db.delete(infos)
    
        helper.set_status(204)


class ArtifactsSearchHandler(webapp.RequestHandler):
    
    def get(self, **kw):
        helper = RequestHelper(self)
        q = self.request.get("q", None)
        output = self.request.get("o", None)
        max_results = int(self.request.get("max", -1))
        
        if not q:
            helper.error(400, "q not provided.")
            return

        q_results = ArtifactContent.all().search(q)

        json_results = None
        if output == "short":
            json_results = {}
            json_results["count"] = q_results.count()
        elif output == "id":
            json_results = {}
            count = q_results.count()
            if max_results > 0 and max_results < q_results.count():
                count = max_results
                
            json_results["count"] = count
            ids = []
            json_results["ids"] = ids
            results = q_results.fetch(1000) if max_results == -1 else q_results.fetch(max_results)
            for c in results:
                ids.append(c.guid)
        else:
            json_results = []
            if q_results.count():
                for content in q_results.fetch(10):
                    info = ArtifactInfo.get_by_guid(content.guid)
                    json_results.append(ArtifactsHelper.artifact_to_hash(info, content))
        helper.write_json(json_results)

    def delete(self, **kw):
      helper = RequestHelper(self)
      q = self.request.get("q", None)
      if not q:
        helper.error(400, "q not provided.")
        return

      results = {}
      deleted_guids = []
      results["deleted"] = deleted_guids
      errors = 0
      q_results = ArtifactContent.all().search(q)
      
      infos = []
      batch_size = 50
      q_count = q_results.count()
      batches = (q_count / batch_size) + 1
      count = 0
      for i in range(0, batches):
        for c in q_results.fetch(batch_size, i * batch_size):
          try:
            logging.debug("deleting guid:%s" % c.guid)
            c.delete()
            count += 1
            deleted_guids.append(c.guid)
            if c.info is not None:
              c.info.delete()              
          except Exception, ex:
            logging.error(ex)
            errors += 1
              
      results["deleted_count"] = count
      results["errors"] = errors

      helper.write_json(results)


class ArtifactHandler(webapp.RequestHandler):
    
    def get(self, guid, **kw):
        ArtifactsHelper.get(self, guid)
        
    def delete(self, guid, **kw):
        ArtifactsHelper.delete(self, guid)
        
    def put(self, guid, **kw):
        ArtifactsHandler.put(self, guid)
