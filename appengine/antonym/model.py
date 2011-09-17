import logging

from google.appengine.ext import db, search
from google.appengine.api import users

from katapult.log import LoggerFactory
from katapult.models import entity_has_property, IdGenerator

from antonym.core import IllegalArgumentException, NotFoundException


def strict_key_lookup():
    """
    decorator to return single entity for single key-like param, or fail.
    
    keywords:
        return_none - True if method should return none instead of raising NotFoundException (defaults to False)
    raises:
        NotFoundException
    """
    def func_wrapper(f):
        def args_wrapper(*args, **kw):
            return_none = kw.pop("return_none", False)
            cls = args[0]
            key_arg = args[1]
            entities = f(*args, **kw)
            if not entities:
                if return_none:
                    result = None
                else:
                    raise NotFoundException("%s %s" % (cls.__name__, key_arg))
            else:
                result = entities
            return result
        return args_wrapper
    return func_wrapper

def single_result_query():
    """ decorator enforces that query returned by wrapped method returns only one result """
    def func_wrapper(f):
        def args_wrapper(*args, **kw):
            return_none = kw.pop("return_none", False)
            cls = args[0]
            q = f(*args, **kw)
            q_count = q.count()
            result = None
            if not q_count:
                if not return_none:
                    raise NotFoundException("%s query" % cls.__name__)
            elif q_count > 1:
                raise DuplicateDataException("%s query" % cls.__name__)
            else:
                result = q.fetch(1)[0]
            return result
        return args_wrapper
    return func_wrapper


class ArtifactSource(db.Model):

    name = db.StringProperty(required=True)

    @classmethod
    @strict_key_lookup()
    def get_by_name(cls, name, **kw):
        return cls.get_by_key_name(name, **kw)

    @classmethod
    @strict_key_lookup()
    def get_multiple_by_name(cls, *names, **kw):
        return cls.get_by_key_name(names, **kw)
        
    @classmethod
    def get_or_create(cls, name):
        """
        returns:
            source key
        """
        source = cls.get_by_name(name, return_none=True)
        return source.key() if source else cls.create(name)

    @classmethod
    def create(cls, name):
        return cls(key_name=name, name=name).put()

    def __repr__(self):
        return "%s{name='%s'}" % (self.__class__.__name__, self.name)


class UrlResource(db.Model):
    
    url = db.StringProperty(required=True)
    modified = db.DateTimeProperty(required=True, auto_now=True)
    source_modified = db.DateTimeProperty()
    etag = db.StringProperty()
    
    # TODO: how to create bidirectional references between Feed and UrlResource?
    feed = db.ReferenceProperty()

    @classmethod
    @strict_key_lookup()
    def get_by_url(cls, url, **kw):
        return cls.get_by_key_name(url)
        
    @classmethod
    def create(cls, url, **kw):
        return cls(key_name=url, url=url, **kw).put()

    @classmethod
    def find_latest(cls, **kw):
        return cls.all().order("-modified")

    @classmethod
    def search_by_url(cls, url_regex, **kw):
        for u in cls.all().fetch(1000):
            if url_regex.search(u.url):
                yield u


class Feed(db.Model):
    
    url = db.StringProperty(required=True)
    artifact_source = db.ReferenceProperty(ArtifactSource, required=True)
    url_resource = db.ReferenceProperty(UrlResource, required=True)
    active = db.BooleanProperty(required=True)
    
    @classmethod
    @strict_key_lookup()
    def get_by_source_name(cls, source_name, **kw):
        return cls.get_by_key_name(source_name)

    @classmethod
    def get_by_url(cls, url, **kw):
        return cls.all(**kw).filter("url =", url)

    @classmethod    
    @single_result_query()
    def get_by_source(cls, source, **kw):
        return cls.all(**kw).filter("artifact_source =", source)

    @classmethod
    def find_active(cls, **kw):
        return cls.all(**kw).filter("active =", True)
        
    @classmethod
    def create(cls, source_name, **kw):
        return cls(key_name=source_name, **kw).put()


class ArtifactInfo(db.Model):

    # identifier.  will be the same for matching ArtifactContent instance.
    guid = db.StringProperty(required=True)
    
    source = db.ReferenceProperty(ArtifactSource, required=True)
    source_name = db.StringProperty(required=True)
    content_type = db.StringProperty(required=True)
    modified = db.DateTimeProperty(required=True, auto_now_add=True)
    modified_by = db.UserProperty(required=True)
    
    content_md5 = db.StringProperty(required=True)
    
    # references the source resource
    # TODO: why does artifactinfo_set exist, I see no ReferenceProperties implying its existence
    url = db.StringProperty()
    url_resource = db.ReferenceProperty(UrlResource, collection_name="artifactinfo_set2")
    
    @classmethod
    def create(cls, **kw):
        guid = IdGenerator.uuid()
        return cls(key_name=guid, guid=guid, **kw).put()

    @classmethod
    def get_by_guid(cls, guid):
        return cls.get_by_key_name(guid)

    @classmethod
    def find_by_source(cls, source, **kw):
        return cls.all(**kw).filter("source =", source)

    @classmethod
    def find_by_content_md5(cls, md5, **kw):
        return cls.all(**kw).filter("content_md5 =", md5)

    @classmethod
    def find_newer(cls, datetime, **kw):
        return cls.all(**kw).filter("modified > ", datetime)

    @classmethod
    def find_by_source_in_reverse_modified_order(cls, source, **kw):
        return cls.all(**kw).filter("source =", source).order("-modified")
        
    @classmethod
    def delete_oldest_by_source(cls, source, keep_count, max_delete=500):
        keys = cls.find_by_source_in_reverse_modified_order(source, keys_only=True).fetch(max_delete, keep_count)
        key_names = [m.name() for m in keys]
        db.delete(keys)
        return key_names


class ArtifactContent(search.SearchableModel):

    # identifier.  will be the same for matching ArtifactInfo instance.
    guid = db.StringProperty(required=True)
    
    source = db.ReferenceProperty(ArtifactSource, required=True)
    source_name = db.StringProperty(required=True)
    
    info = db.ReferenceProperty(ArtifactInfo, required=True)
    body = db.TextProperty(required=True)
    
    # TODO: make required
    modified = db.DateTimeProperty(auto_now_add=True)
    
    @classmethod
    def create(cls, guid, **kw):
        return cls(key_name=guid, guid=guid, **kw).put()

    @classmethod
    def get_by_guid(cls, guid):
        return cls.get_by_key_name(guid)

    @classmethod
    def find_by_source(cls, source):
        return cls.all().filter("source =", source)
        
    @classmethod
    def find_by_source_in_reverse_modified_order(cls, source, **kw):
        return cls.all(**kw).filter("source =", source).order("-modified")
        
    @classmethod
    def delete_oldest_by_source(cls, source, keep_count, pre_call=None, max_delete=500):
        models = cls.find_by_source_in_reverse_modified_order(source).fetch(max_delete, keep_count)
        key_names = []
        for m in models:
          try:
            key_name = m.key().name()
            if pre_call:
              pre_call(m)
            m.delete()
            key_names.append(key_name)
          except Exception, e:
            logging.error(e)
        return key_names

    def __repr__(self):
        return "%s(guid=%s, source=%s, body=%s)" % \
            (self.__class__.__name__, self.guid, self.source_name, self.body)


class TwitterResponse(db.Model):
    
    MENTION = 'mention'
    DIRECT = 'direct'
    RETWEET = 'retweet'
    
    # TODO: are there conflicts between direct message ids and public status ids?
    
    # twitter ids
    message_id = db.StringProperty(required=True)
    response_id = db.StringProperty(required=True)
    
    # twitter user
    user = db.StringProperty(required=True)
    
    # can't be required, since this was added for retweets
    tweet_type = db.StringProperty(set([MENTION, DIRECT, RETWEET]))
    
    timestamp = db.DateTimeProperty(required=True, auto_now_add=True)

    @classmethod
    def get_by_message_id(cls, message_id):
        return cls.get_by_key_name(message_id)
    
    @classmethod
    def create(cls, message_id, **kw):
        return cls(key_name=message_id, message_id=message_id, **kw).put()

    @classmethod
    def find_latest(cls, **kw):
        return cls.all().order("-timestamp")


class Configuration(db.Model):

    twitter_access_token = db.StringProperty()
    twitter_oauth_enabled = db.StringProperty()
    is_tweeting = db.StringProperty()
    twitter_read_only = db.StringProperty(default="1")
    
    @classmethod
    def _key_name(cls):
        return cls.__name__
        
    @classmethod
    def get(cls):
        return cls.get_by_key_name(cls._key_name())
    
    @classmethod
    def get_or_create(cls):
        c = cls.get()
        if not c:
            c = cls._new()
            c.put()
        return c
    
    @classmethod
    def _new(cls):
        return cls(key_name=cls._key_name())
        
    @classmethod
    def update(cls, **kw):
        entity = cls.get()
        if not entity:
            entity = cls._new()
        defined_props = entity.properties()
        for k, v in kw.iteritems():
            logging.info("%s %s=%s" % (cls._key_name(), k, v))
            if not k in defined_props:
                raise IllegalArgumentException("invalid field: %s" % k)
            setattr(entity, k, v)
        return entity.put()
