import hashlib

from google.appengine.ext import db

import simplejson as json

from antonym.core import DataException, DuplicateDataException, IllegalArgumentException, MissingDataException, NotFoundException
from antonym.text.markov import Markov2Speaker, TwittovSpeaker
from antonym.text.rewriting import RegexRewriter
from antonym.model import ArtifactContent, ArtifactInfo, ArtifactSource

from katapult.accessors.counters import Counter
from katapult.log import LoggerFactory
from katapult.models import Models


class Counters:

    @classmethod
    def source_counter(cls, source_name):
        return Counter(json.dumps({'source': source_name}))


class ArtifactSourceAccessor:
    
    @classmethod
    def delete(cls, source_name):
        source = ArtifactSource.get_by_name(source_name)
        if not source:
            raise NotFoundException('ArtifactSource %s' % source_name)
            
        # finds all deletes artifacts for source
        info_keys = ArtifactInfo.find_by_source(source, keys_only=True)
        content_keys = ArtifactContent.find_by_source(source)
        
        # zips keys so they are in pairs
        for artifact_keys in zip(info_keys, content_keys):
            db.delete(artifact_keys)
        
        # deletes source
        db.delete(source)


class ArtifactAccessor:
    
    @classmethod
    def _content_md5(cls, source_name, content_type, body):
        hasher = hashlib.md5()
        hasher.update("%s;%s;%s" % (source_name, content_type, body))
        return hasher.hexdigest()
    
    @classmethod
    def save(cls, **kw):
        """
        returns:
            tuple: (ArtifactInfo key, ArtifactContent key, ArtifactSource key)
        raises:
            DuplicateDataException - if artifact already exists
        """
        if not kw:
            raise IllegalArgumentException("keywords must be provided")
            
        source_name = kw.pop("source", None)
        content_type = kw.get("content_type")
        
        if not source_name:
            raise IllegalArgumentException("source keyword must be provided.")
        elif not content_type:
            raise IllegalArgumentException("content_type keyword must be provided.")
            
        # I pop "body" since I can't include it as a keyword for ArtifactInfo.save()
        body = kw.pop("body", None)

        # hashes content to avoid saving a duplicate
        content_md5 = cls._content_md5(source_name, content_type, body)
        
        found_artifact_key = ArtifactInfo.find_by_content_md5(content_md5, keys_only=True).get()
        if found_artifact_key:
            raise DuplicateDataException("artifact %s" % (found_artifact_key.name()))

        # saves source, if unique
        source_key = ArtifactSource.get_or_create(source_name)
        
        # bump source counter
        Counters.source_counter(source_name).increment()
        
        # saves ArtifactInfo
        a_info_key = ArtifactInfo.save(content_md5=content_md5,
            source=source_key,
            source_name=source_name,
            **kw)

        # saves ArtifactContent
        guid = a_info_key.name()
        a_content_key = ArtifactContent.save(guid,
            body=body,
            source=source_key,
            source_name=source_name,
            info=a_info_key)
                
        return a_info_key, a_content_key, source_key

    @classmethod
    def delete(cls, guid):
        logger = LoggerFactory.logger(cls.__name__)
        
        a_info = ArtifactInfo.get_by_guid(guid)
        a_content_key = ArtifactContent.get_by_guid(guid)
        if not (a_info or a_content_key):
            # neither record found
            raise NotFoundException("artifact %s" % guid)
        elif not (a_info and a_content_key):
            # one record found; one missing
            logger.warn("artifact %s; missing data; info=%s; content=%s" % (guid, a_info.key().name(), a_content_key))
        
        # I delete what I can
        keys = []
        if a_info: keys.append(a_info)
        if a_content_key: keys.append(a_content_key)
        
        db.delete(keys)

        # decrease source counter
        Counters.source_counter(a_info.source.name).decrement()


class MixtureAccessor:
    
    MINIMUM_ARTIFACTS = 10
    
    # only map people that are following livelock
    _twitter_user_rewriter = RegexRewriter({ r'jvolkman:?': '@jvolkman',
        r'mhawthorne:?': '@mhawthorne',
        r'mmattozzi:?': '@mikemattozzi'})
    
    @classmethod
    def mix(cls, **kw):
        """
        keywords:
            source_name
            
        raises:
            DataException if no content is found
        """
        logger = LoggerFactory.logger(cls.__name__)
        source_name = kw.get("source_name", None)
        
        if source_name:
            source = ArtifactSource.get_by_name(source_name)
        else:
            # choose random source
            source_q = ArtifactSource.all()
            if not source_q.count():
                raise MissingDataException("no ArtifactSources found")
            
            source = Models.find_random(source_q, 1).pop()
            
        logger.debug("source: %s" % source.name)
        
        # choose random artifacts for source
        content_q = ArtifactContent.all().filter("source =", source)
        content_q_count = content_q.count()
        if content_q_count < cls.MINIMUM_ARTIFACTS:
            msg = "not enough ArtifactContents found for ArtifactSource %s (%d < %d)" % \
                (source.name, content_q_count, cls.MINIMUM_ARTIFACTS)
            logger.error(msg)
            raise MissingDataException(msg)
            
        a_contents = Models.find_random(content_q, 500)
        
        content = cls._twitter_user_rewriter.rewrite(cls._markov_content(a_contents))
        return source, content

    @classmethod
    def _random_content(cls, contents):
        return contents[0].body
    
    @classmethod
    def _markov_content(cls, contents):
        speaker = Markov2Speaker()
        for content in contents:
            speaker.ingest(content.body)
        return speaker.speak(50, 130)
