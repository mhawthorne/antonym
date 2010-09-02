import hashlib
import logging
import traceback

from google.appengine.ext import db

import simplejson as json

from antonym.accessors import ArtifactAccessor
from antonym.core import DataException, DuplicateDataException, IllegalArgumentException, MissingDataException, NotFoundException
from antonym.text.rewriting import RegexRewriter
from antonym.model import ArtifactContent, ArtifactInfo, ArtifactSource, TwitterResponse, UrlResource

from katapult.accessors.counters import Counter
from katapult import caching
from katapult.caching import Cache
from katapult.models import random_query_results


class Mixer:
    
    MINIMUM_ARTIFACTS = 1
    
    CONTENT_BATCH_SIZE = 100
    
    _blacklist_phrase = '#hi'
    
    # TODO: make this configurable
    _comcast_blacklist = set([r'excalibur', r'\S*xcal\S*', r'ccp|CCP',
        r'#?[cC]omcast\S*', r'(#?cim|#?CIM)\S*',
        r'#?[fF]ancast\S*', 
        r'(the ?)?[pP]latform',
        r'[xX]finity\S*',
        r'm?horwitz', r'[bB]ad ?[dD]og', r'BD',
        r'[jJ]ason [pP]ress', r'jpress',
        r'amy banse', r'sam schwartz', r'bruce'
    ])

    # relax, I'm half black
    _political_blacklist = set([r'[nN][iI][gG]{2}[eE][rR]', r'[nN][iI][gG]{2}[aA]'])
    
    _blacklist_regexes = _comcast_blacklist | _political_blacklist
    
    _rewrite_map = {
        r'aevans:?': '@aaronte',
        r'arpit:?': '@arpit',
        r'bschmaus:?': '@schmaus',
        r'dillera?:?': '@dillera',
        r'jho:?': '@jho255',
        r'(j(onj)?lee|jlee):?': '@jonjlee',
        r'jvolkman:?': '@jvolkman',
        r'mblinn:?': '@NovusTiro',
        r'mhawthorne:?': '@mhawthorne',
        r'(mmattozzi|cimmy|sonofcim):?': '@mikemattozzi',
        r'mschaffer:?': '@matschaffer',
        r'ohpauleez:?': '@ohpauleez',
        r'vfumo:?': '@neodem',
    }
    
    for b in _blacklist_regexes:
        _rewrite_map[b] = _blacklist_phrase
    
    # maps #milhouse names (or other names that I've ingested to twitter names)
    _twitter_user_rewriter = RegexRewriter(_rewrite_map)
    
    # will this let me mock a Mixer?
    @classmethod
    def new(cls, speaker):
        return Mixer(speaker, from_factory=True)
        
    def __init__(self, speaker, **kw):
        if not "from_factory" in kw:
            raise IllegalArgumentException("constructor should not be called directly")

        self.__speaker = speaker
    
    def mix_sources(self, *source_names):
        sources = ArtifactSource.get_multiple_by_name(*source_names)
        missing = filter(lambda i: i is None, sources)
        if missing:
            raise NotFoundException("1 or more sources not found: %s" % source_names)
        return self.__random_content_for_sources(sources)
        
    def mix_random_limit_sources(self, source_count, degrade=False):
        """
        params:
            source_count - number of sources to mix
            degrade - if True, mix even if source_count sources cannot be found
        returns:
            ((sources), mixed_content)
        """
        # choose random sources
        source_q = ArtifactSource.all()
        q_count = source_q.count()
        if (q_count < source_count):
            if degrade:
                logging.debug("mix_random_limit_sources requested %d sources; degrading to %d" % (source_count, q_count))
                source_count = q_count
            else:
                raise MissingDataException("insufficient ArtifactSources found (%d < %d)" % \
                    (q_count, source_count))
        sources = random_query_results(source_q, source_count)
        return self.__random_content_for_sources(sources)

    def mix_latest(self):
        q = ArtifactContent.all().order("-modified")
        contents = self.__random_content_from_query(q)
        return self.__mix_contents(contents)
        
    def mix_after_search(self, term, **kw):
        contents = ArtifactAccessor.search(term)
        return self.__mix_contents(contents, **kw)        
        
    def mix_response(self, message, min_results=10, **kw):
        # find longest word in message
        words = [w for w in message.split()]
        sorted_words = sorted(words, key=lambda w: len(w), reverse=True)
                
        # searches from longest word to shortest until result count > min result threshold
        contents = []
        for w in sorted_words:
            results = ArtifactAccessor.search(w)
            logging.debug("search for '%s' found %d result(s)" % (w, len(results)))
            contents.extend(results)
            if len(contents) >= min_results:
                break

        are_results_mixed = False
        if contents:
            # mix search results
            try:
                result = self.__mix_contents(contents, **kw)
                are_results_mixed = True
            except MissingDataException, e:
                logging.error(traceback.print_exc())
        
        # no results were mixed, generate random link or text
        if not are_results_mixed:    
            result = self.__random_text_or_link()

        logging.debug("responding to '%s' with '%s'" % (message, result[1]))
        return result

    def __random_link_or_text(self):
        try:
            result = (), self.random_resource().url
        except MissingDataException, e2:
            logging.error(traceback.print_exc())
            result = self.mix_random_limit_sources(1)
        return result

    def __random_text_or_link(self):
        try:
            result = self.mix_random_limit_sources(1)
        except MissingDataException, e2:
            logging.error(traceback.print_exc())
            result = (), self.random_resource().url
        return result

    def random_resource(self, max_length=130):
        resource = None
        q = UrlResource.find_latest()
        if not q.count():
            raise MissingDataException("no results found")
            
        for resource in random_query_results(q, 10):
            if len(resource.url) < max_length:
                break
        if not resource: raise MissingDataException("no sufficient resources found")
        return resource
        
    def __random_content_for_sources(self, sources, count=CONTENT_BATCH_SIZE):
        """
        returns:
            (list of sources, mixed content string) tuple
        """
        logging.debug("__random_content_for_sources sources:%s" % sources)
        total_contents = []
        for source in sources:
            total_contents.extend(self.__random_content_for_source(source, count))
        return self.__mix_contents(total_contents)
        
    def __random_content_for_source(self, source, count, minimum_results=MINIMUM_ARTIFACTS):
        """
        returns:
            list of ArtifactContent records
        """
        if not source:
            raise IllegalArgumentException("source cannot be None")
            
        logging.debug("__random_content_for_source source:%s" % source)
        content_q = ArtifactContent.all().filter("source =", source)
        content_q_count = content_q.count()
        if content_q_count < minimum_results:
            msg = "not enough ArtifactContents found for ArtifactSource %s (%d < %d)" % \
                (source.name, content_q_count, minimum_results)
            raise MissingDataException(msg)
        return random_query_results(content_q, count)
        
    def __random_content_from_query(self, q, count=CONTENT_BATCH_SIZE, minimum_results=MINIMUM_ARTIFACTS):
        """
        returns:
            list of ArtifactContent records
        """
        q_count = q.count()
        if q_count < minimum_results:
            msg = "not enough ArtifactContents found in query (%d < %d)" % \
                (q_count, minimum_results)
            logging.error(msg)
            raise MissingDataException(msg)
        return random_query_results(q, count)
        
    def __mix_contents(self, contents, **kw):
        """
        returns:
            (soures, content) tuple
        """
        sources, raw_content = self.__mix_content(contents, **kw)
        return sources, self._twitter_user_rewriter.rewrite(raw_content)

    def __mix_content(self, contents, **kw):
        """
        returns:
            (sources, content) tuple
        """
        min_length = kw.pop("min_length", 2)
        max_length = kw.pop("max_length", 130)
        sources = {}
        
        for content in contents:
            source_name = content.source_name
            body = content.body
            if not sources.has_key(source_name):
                sources[source_name] = content.source
            logging.debug("__mix_content body:%s" % body)
            self.__speaker.ingest(body)
        return sources.values(), self.__speaker.speak(min_length, max_length)