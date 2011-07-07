from datetime import date, datetime, time
import logging
import sys

from google.appengine.ext import webapp

from katapult.reflect import get_full_class_name
from katapult.requests import RequestHelper

from antonym.accessors import ArtifactAccessor, ArtifactSourceAccessor
from antonym.ttwitter import describe_status_with_timestamp, TwitterActor, TwitterException


class StatsHandler(webapp.RequestHandler):
    
    def get(self):
        helper = RequestHelper(self)
        result = {}
        
        today = datetime.combine(datetime.now(), time(0, 0, 0))
        result['timestamp'] = str(datetime.now())
        result['today'] = str(today)
        
        warnings = []
        result['warnings'] = warnings
        
        # source/artifact counts
        result['source_artifact_counts'] = ArtifactSourceAccessor.find_artifact_counts()
        
        # new artifacts
        result['new_artifacts'] = ArtifactSourceAccessor.find_artifact_counts_newer(today)
        
        # newer_arts = ArtifactAccessor.find_newer(today, refresh=True)
        
        # new_art_stats = []
        # result['new_artifacts'] = new_art_stats
                
        # for art in newer_arts:
        #     new_art_stats.append(dict(guid=art.guid, source_name=art.source_name))
        
        try:
            twactor = TwitterActor()
            
            # outgoing messages
            result['statuses_out'] = [describe_status_with_timestamp(s) for s in twactor.latest_statuses(5)]
            
            # incoming messages
            direct_stats = []
            mention_stats = []
            result['directs'] = direct_stats
            result['mentions'] = mention_stats
        
            directs, mentions = twactor.messages(today)
            directs.reverse()
            mentions.reverse()
            direct_stats.extend([describe_status_with_timestamp(s) for s in directs])
            mention_stats.extend([describe_status_with_timestamp(s) for s in mentions])
        except TwitterException, ex:
            warnings.append(str(ex))

        helper.write_json(result)