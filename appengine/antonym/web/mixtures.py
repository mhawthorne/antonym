import logging
import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import simplejson as json

# I need to reference functions from the module instead of importing them directly
# so that I can mock them (strange)
from antonym.mixer import Mixer
from antonym.text.speakers import new_speaker, new_random_speaker

from antonym.core import NotFoundException

from katapult.core import DataException, Exceptions, Hashes
from katapult import log
from katapult.models import Models
from katapult.requests import time_request, RequestHelper


class MixtureHandler(webapp.RequestHandler):
    
    def get(self, source_name, **kw):
        helper = RequestHelper(self)

        try:
            speaker_name = self.request.get("s", None)
            if speaker_name:
                speaker = new_speaker(speaker_name)[1]
                mixer = Mixer.new(speaker)
            else:
                speaker_name, speaker = new_random_speaker()
                logging.debug("speaker: %s" % str(speaker))
                mixer = Mixer(speaker)
        
            # direct message
            message = self.request.get("q", None)
            if message:
                message = urllib.unquote(message)
                sources, content = mixer.mix_response(message)
            else:
                if not source_name:
                    sources, content = mixer.mix_random_limit_sources(2, degrade=True)
                else:
                    source_name = urllib.unquote(source_name)
                    logging.debug("get source_name: %s" % source_name)
                    if ";" in source_name:
                        # multiple sources
                        sources_split = set(source_name.split(";"))
                        sources, content = mixer.mix_sources(*sources_split)
                    else:
                        # single source
                        sources, content = mixer.mix_sources(source_name)
            logging.debug("sources: %s" % str(sources))
            source_hash_list = [s.name for s in sources]
            mix_hash = {"sources": source_hash_list,
                "speaker": {"name": speaker_name, "id": hash(speaker), "details": str(speaker)},
                "body": content}
            helper.write_json(mix_hash)
        except NotFoundException, ex:
            helper.error(404, Exceptions.format(ex))
            logging.error(ex)
        except DataException, ex:
            helper.error(503, Exceptions.format(ex))
            logging.error(ex)


class MixtureResponseHandler(webapp.RequestHandler):
    """ invoked from UI shell """
    
    def get(self, **kw):
        helper = RequestHelper(self)
        message = self.request.get("q", None)
        if not message:
            helper.error(400, "q must be provided")
            return
        message = urllib.unquote(message)
        try:
            sources, response = Mixer(new_speaker()).mix_response(message)
            logging.debug("sources:%s, response:%s" % (sources, response))
            result = dict(response=response)
            helper.write_json(result)
        except DataException, ex:
            helper.error(503, Exceptions.format(ex))
            logging.error(ex)
        

