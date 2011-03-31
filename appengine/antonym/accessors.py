import hashlib
import logging

from google.appengine.ext import db

import simplejson as json

from antonym.core import ConflictingDataException, DataException, DuplicateDataException,\
    IllegalArgumentException, MissingDataException, NotFoundException
from antonym.text.rewriting import RegexRewriter
from antonym.model import ArtifactContent, ArtifactInfo, ArtifactSource, Configuration, Feed, TwitterResponse, UrlResource

from katapult.accessors.counters import Counter
from katapult.caching import decorators as caching
from katapult.log import LoggerFactory
from katapult.models import Models


class Counters:

    @classmethod
    def source_counter(cls, source_name):
        return Counter(json.dumps({'source': source_name}))


def _artifact_source_cache_key(*args, **kw):
    return "source=%s" % args[1]


class ArtifactSourceAccessor:
        
    @classmethod
    @caching.cache_return_by_argument_key(_artifact_source_cache_key)
    def get_by_name(cls, source_name, **kw):
        return ArtifactSource.get_by_name(source_name, **kw)
    
    @classmethod
    @caching.cache_delete_by_argument_key(_artifact_source_cache_key)
    def delete_by_name(cls, source_name):
        source = ArtifactSource.get_by_name(source_name)
        logging.debug("delete_by_name source: %s" % source)
        if not source:
            raise NotFoundException('ArtifactSource %s' % source_name)
            
        # checks for feeds linked to source
        feed = FeedAccessor.get_by_source_name(source_name, return_none=True)
        if feed:
            raise ConflictingDataException("ArtifactSource '%s' is referenced by Feed '%s'" % (source_name, feed.url))
        
        # finds and deletes artifacts for source
        info_keys = ArtifactInfo.find_by_source(source, keys_only=True)
        content_keys = ArtifactContent.find_by_source(source)
        
        # zips keys to delete info/content pairs back-to-back
        for artifact_keys in zip(info_keys, content_keys):
            db.delete(artifact_keys)
        
        # deletes source
        db.delete(source)

    @classmethod
    def create(cls, source_name, **kw):
        return ArtifactSource.create(source_name, **kw)


class UrlResourceAccessor:
    
    @classmethod
    @caching.cache_return_by_argument_key(lambda *args, **kw: "url-resource:%s" % args[1])
    def get_by_url(cls, url, **kw):
        return UrlResource.get_by_url(url, **kw)

    @classmethod
    def create(cls, url, **kw):
        return UrlResource.create(url, **kw)

    @classmethod
    def get_or_create(cls, url, **kw):
        u = cls.get_by_url(url, return_none=True)
        if not u:
            # returns key
            u_key = cls.create(url, **kw)
            # looks up url for key
            u = UrlResource.get(u_key)
        return u

    # @classmethod
    # def delete(cls, url_resource):

    @classmethod
    @caching.cache_return_by_argument_key(lambda *args, **kw: "url-resource:search=%s" % args[1])
    def search_by_url(cls, term, **kw):
        return [u for u in UrlResource.search_by_url_regex(term)]


class ArtifactAccessor:
    
    @classmethod
    def _content_md5(cls, source_name, content_type, body):
        logger = LoggerFactory.logger(cls.__name__)
        # logger.debug("%s, %s, %s" % (source_name.__class__, content_type.__class__, body.__class__))
        hasher = hashlib.md5()
        hasher.update("%s;%s;%r" % (source_name, content_type, body))
        return hasher.hexdigest()
    
    @classmethod
    @caching.cache_return_by_argument_key(lambda *args, **kw: "artifact:content:%s" % args[1])
    def get_content_by_guid(cls, guid):
        return ArtifactContent.get_by_guid(guid)
        
    @classmethod
    def find_or_create(cls, **kw):
        """
        returns:
            tuple: (ArtifactInfo key, ArtifactContent key, ArtifactSource key, created)
        """
        if not kw:
            raise IllegalArgumentException("keywords must be provided")
            
        source_name = kw.pop("source", None)
        content_type = kw.get("content_type")
        
        if not source_name:
            raise IllegalArgumentException("source keyword must be provided.")
        elif not content_type:
            raise IllegalArgumentException("content_type keyword must be provided.")
            
        # I pop "body" since I can't include it as a keyword for ArtifactInfo.create()
        body = kw.pop("body", None)

        # hashes content to avoid saving a duplicate
        content_md5 = cls._content_md5(source_name, content_type, body)
        
        found_artifact = ArtifactInfo.find_by_content_md5(content_md5).get()
        if found_artifact:
            info_key = found_artifact.key()
            content_key = ArtifactContent.get_by_guid(found_artifact.guid).key()
            source_key = found_artifact.source.key()
            created = False
        else:
            info_key, content_key, source_key = cls._create(source_name, body, content_md5, **kw)
            created = True
        return (info_key, content_key, source_key, created)
        
    @classmethod
    def create(cls, **kw):
        """
        keywords:
            source
            content_type
            body
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
            
        # I pop "body" since I can't include it as a keyword for ArtifactInfo.create()
        body = kw.pop("body", None)

        # hashes content to avoid saving a duplicate
        content_md5 = cls._content_md5(source_name, content_type, body)
        
        found_artifact_key = ArtifactInfo.find_by_content_md5(content_md5, keys_only=True).get()
        if found_artifact_key:
            raise DuplicateDataException("artifact %s" % (found_artifact_key.name()))

        return cls._create(source_name, body, content_md5, **kw)
        
    @classmethod
    def _create(cls, source_name, body, content_md5, **kw):
        # saves source, if unique
        source_key = ArtifactSource.get_or_create(source_name)
        
        # saves ArtifactInfo
        a_info_key = ArtifactInfo.create(content_md5=content_md5,
            source=source_key,
            source_name=source_name,
            **kw)

        # saves ArtifactContent
        guid = a_info_key.name()
        a_content_key = ArtifactContent.create(guid,
            body=body,
            source=source_key,
            source_name=source_name,
            info=a_info_key)
            
        # bump source counter
        # it's important to do this AFTER the artifacts are saved
        Counters.source_counter(source_name).increment()
                
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

    # NOTE: when max_results was 100, I occassionally get a "too large" exception since the value to cache was over 1M.
    
    @classmethod
    @caching.cache_return_by_argument_key(lambda *args, **kw: "artifact-search;term=%s" % args[1])
    def search(cls, term, max_results=50):
        # TODO: tweak result limit
        return [c for c in ArtifactContent.all().search(term).fetch(max_results)]


class FeedAccessor:
    
    @classmethod
    @caching.cache_return_by_argument_key(lambda *args, **kw: "feed:source_name=%s" % args[1])
    def get_by_source_name(cls, source_name, **kw):
        return Feed.get_by_source_name(source_name, **kw)


class TwitterResponseAccessor:
    
    @classmethod
    @caching.cache_return_by_argument_key(lambda *args, **kw: "twitter-response;id=%s" % args[1])
    def get_by_message_id(cls, message_id):
        return TwitterResponse.get_by_message_id(message_id)

    @classmethod
    def create(cls, message_id, **kw):
        return TwitterResponse.create(message_id, **kw)


_config_cache_key = "config"

class ConfigurationAccessor:

    @classmethod
    @caching.cache_return_by_argument_key(lambda *args: _config_cache_key)
    def get_or_create(cls):
        return Configuration.get_or_create()
        
    @classmethod
    @caching.cache_delete_by_argument_key(lambda *args, **kw: _config_cache_key)
    def update(cls, **kw):
        logging.info("ConfigurationAccessor update %s" % kw)
        Configuration.update(**kw)
