import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from katapult.requests import RequestHelper

from antonym.accessors import ArtifactSourceAccessor, Counters
from antonym.core import NotFoundException
from antonym.model import ArtifactInfo, ArtifactSource, Feed
from antonym.web.services import require_service_user


def source_hash(source):
    c = Counters.source_counter(source.name)
    return { 'name': source.name,
            'count': c.count(),
            'content-count': ArtifactSourceAccessor.count_content(source),
            'info-count': ArtifactSourceAccessor.count_infos(source)
            }
    
    
class SourcesHandler(webapp.RequestHandler):
    
    def get(self, **kw):
        helper = RequestHelper(self)
        results = []
        for s in ArtifactSource.all().fetch(100, 0):
            results.append(source_hash(s))
        helper.write_json(results)


class SourceHandler(webapp.RequestHandler):
    
    def get(self, name, **kw):
        helper = RequestHelper(self)
        source = ArtifactSourceAccessor.get_by_name(name, return_none=True)
        if not source:
            helper.error(404)
            return
        helper.write_json(source_hash(source))

    def put(self, name, **kw):
        helper = RequestHelper(self)
        source = ArtifactSourceAccessor.get_by_name(name, return_none=True)
        if source:
            helper.set_status(409, "duplicate ArtifactSouce")
            return
        ArtifactSourceAccessor.create(name)
        helper.set_status(204)
            
    def delete(self, name, **kw):
        helper = RequestHelper(self)
        try:
            ArtifactSourceAccessor.delete_by_name(name)
            helper.set_status(204)
        except NotFoundException, ex:
            helper.error(404)
            return


class SourceCleanerHandler(webapp.RequestHandler):
    
    # @require_service_user()
    def post(self, **kw):
        helper = RequestHelper(self)
        results = {}
        source_q = ArtifactSource.all()
        for s in source_q:
            artifact_q = ArtifactInfo.find_by_source(s)
            count = len([a for a in artifact_q])
            counter = Counters.source_counter(s.name)
            old_count = counter.count()
            counter.set(count)
            
            source_result = { 'old': old_count }
            
            # if source is linked to a feed, I can't delete it
            feed = Feed.get_by_source(s, return_none=True)
            if feed:
                source_result['feed'] = feed.url

            if not count and not feed:
                s.delete()
                source_result['deleted'] = True
            
            if count:
                source_result['new'] = count
                
            results[s.name] = source_result
        helper.write_json(results)

