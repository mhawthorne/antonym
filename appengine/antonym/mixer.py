import hashlib
import logging

from google.appengine.ext import db

import simplejson as json

from antonym.core import DataException, DuplicateDataException, IllegalArgumentException, MissingDataException, NotFoundException
from antonym.text.markov import Markov2Speaker, TwittovSpeaker
from antonym.text.rewriting import RegexRewriter
from antonym.model import ArtifactContent, ArtifactInfo, ArtifactSource, TwitterResponse, UrlResource

from katapult.accessors.counters import Counter
from katapult import caching
from katapult.caching import Cache
from katapult.models import Models


class Mixer:
    
    MINIMUM_ARTIFACTS = 10
    
    CONTENT_BATCH_SIZE = 100
    
    # only map people that are following livelock
    _twitter_user_rewriter = RegexRewriter({ r'jvolkman:?': '@jvolkman',
        r'mhawthorne:?': '@mhawthorne',
        r'mmattozzi:?': '@mikemattozzi'})
    
    @classmethod
    def mix_single(cls, source_name):
        """
        returns:
            source, mixed_content
        raises:
            DataException if no content is found
        """
        source = ArtifactSource.get_by_name(source_name)
        a_contents = cls._random_content_for_source(source, cls.CONTENT_BATCH_SIZE)
        mixed_content = cls._mix_contents(a_contents)
        return source, mixed_content
        
    @classmethod
    def mix_multiple(cls, *source_names):
        sources = ArtifactSource.get_by_name(*source_names)
        return cls._random_content_for_sources(sources, cls.CONTENT_BATCH_SIZE)
        
    @classmethod
    def mix_random_limit_sources(cls, source_count):
        """
        returns:
            ((sources), mixed_content)
        """
        # choose random sources
        source_q = ArtifactSource.all()
        q_count = source_q.count()
        if q_count < source_count:
            raise MissingDataException("insufficient ArtifactSources found (%d < %d)" % \
                (q_count, source_count))
        sources = Models.find_random(source_q, source_count)
        return cls._random_content_for_sources(sources)

    @classmethod
    def mix_random(cls):
        # TODO: randomize ordering of query?
        q = ArtifactContent.all().order("-modified")
        contents = cls._random_content_from_query(q)
        return cls._mix_contents(contents)
        
    @classmethod
    def mix_after_search(cls, term):
        q = ArtifactContent.all().search(term)
        contents = cls._random_content_from_query(q)
        return cls._mix_contents(contents)        

    @classmethod
    def _random_content_for_sources(cls, sources, count):
        """
        returns:
            (list of sources, mixed content string) tuple
        """
        total_contents = []
        for source in sources:
            total_contents.extend(cls._random_content_for_source(source, count))
        mixed_content = cls._mix_contents(total_contents)
        return (sources, mixed_content)
        
    @classmethod
    def _random_content_for_source(cls, source, count):
        """
        returns:
            list of ArtifactContent records
        """
        content_q = ArtifactContent.all().filter("source =", source)
        content_q_count = content_q.count()
        if content_q_count < cls.MINIMUM_ARTIFACTS:
            msg = "not enough ArtifactContents found for ArtifactSource %s (%d < %d)" % \
                (source.name, content_q_count, MINIMUM_ARTIFACTS)
            raise MissingDataException(msg)
        return Models.find_random(content_q, count)
        
    @classmethod
    def _random_content_from_query(cls, q):
        """
        returns:
            list of ArtifactContent records
        """
        q_count = q.count()
        if q_count < cls.MINIMUM_ARTIFACTS:
            msg = "not enough ArtifactContents found in query (%d < %d)" % \
                (q_count, cls.MINIMUM_ARTIFACTS)
            logging.error(msg)
            raise MissingDataException(msg)
        return Models.find_random(q, cls.CONTENT_BATCH_SIZE)
        
    @classmethod
    def mix_response(cls, message):
        """
        returns:
            string
        """
        # find longest word in message
        words = [w for w in message.split()]
        sorted_words = sorted(words, key=lambda w: len(w), reverse=True)
        longest_word = sorted_words[0]
        return cls.mix_after_search(longest_word)
    
    @classmethod
    def _mix_contents(cls, contents):
        """
        returns:
            (soures, content) tuple
        """
        sources, raw_content = cls._markov_content(contents)
        return sources, cls._twitter_user_rewriter.rewrite(raw_content)
  
    @classmethod
    def _random_content(cls, contents):
        return contents[0].body
    
    @classmethod
    def _markov_content(cls, contents):
        """
        returns:
            (sources, content) tuple
        """
        sources = {}
        speaker = Markov2Speaker()
        for content in contents:
            if not sources.has_key(content.source_name):
                sources[content.source_name] = content.source
            speaker.ingest(content.body)
        return sources.values(), speaker.speak(50, 130)