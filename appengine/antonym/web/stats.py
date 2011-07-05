from datetime import date, datetime, time
import logging
import sys

from google.appengine.ext import webapp

from katapult.reflect import get_full_class_name
from katapult.requests import RequestHelper

from antonym.accessors import ArtifactAccessor
from antonym.ttwitter import TwitterActor, TwitterException


class StatsHandler(webapp.RequestHandler):
    
    def get(self):
        helper = RequestHelper(self)
        result = {}
        
        today = datetime.combine(datetime.now(), time(0, 0, 0))
        result['timestamp'] = str(datetime.now())
        result['today'] = str(today)
        
        # artifacts
        newer_arts = ArtifactAccessor.find_newer(today, refresh=True)
        
        art_stats = []
        result['artifacts'] = art_stats
        
        warnings = []
        result['warnings'] = warnings
        
        for art in newer_arts:
            art_stats.append(dict(guid=art.guid, source_name=art.source_name))
        
        try:
            # twitter
            direct_stats = []
            mention_stats = []
            result['directs'] = direct_stats
            result['mentions'] = mention_stats
        
            directs, mentions = TwitterActor().messages()
            for d in directs:
                direct_stats.append(d)
            
            # for m in mentions:
        except TwitterException, ex:
            warnings.append(str(ex))

        helper.write_json(result)