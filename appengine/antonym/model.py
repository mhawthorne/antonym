from google.appengine.ext import db, search
from google.appengine.api import users

from katapult.models import IdGenerator

from antonym.core import NotFoundException


class ArtifactSource(db.Model):
    
    name = db.StringProperty(required=True)

    @classmethod
    def get_by_name(cls, name):
        a = cls.get_by_key_name(name)
        if not a:
            raise NotFoundException("%s %s" % (cls.__name__, name))
        return a

    @classmethod
    def get_or_create(cls, name):
        """
        returns:
            source key
        """
        source = cls.get_by_name(name)
        if source:
            key = source.key()
        else:
            key = cls(key_name=name, name=name).put()
        return key
        

class ArtifactInfo(db.Model):

    # identifier.  will be the same for matching ArtifactContent instance.
    guid = db.StringProperty(required=True)
    
    # source = db.StringProperty()
    source = db.ReferenceProperty(required=True)
    
    # TODO: make required
    source_name = db.StringProperty()
    
    content_type = db.StringProperty(required=True)
    
    # TODO: make required
    modified = db.DateTimeProperty(auto_now_add=True)
    
    modified_by = db.UserProperty(required=True)
    
    # this uniquely identifies the content of an artifact.  used to avoid saving duplicate entries.
    # TODO: make required
    content_md5 = db.StringProperty()
    
    @classmethod
    def save(cls, **kw):
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


class ArtifactContent(search.SearchableModel):

    # identifier.  will be the same for matching ArtifactInfo instance.
    guid = db.StringProperty(required=True)
    
    # source = db.StringProperty()
    
    # TODO: make required
    source = db.ReferenceProperty(ArtifactSource)
    
    # TODO: make required
    source_name = db.StringProperty()
    
    info = db.ReferenceProperty(ArtifactInfo, required=True)
    
    body = db.TextProperty(required=True)
    
    @classmethod
    def save(cls, guid, **kw):
        return cls(key_name=guid, guid=guid, **kw).put()

    @classmethod
    def get_by_guid(cls, guid):
        return cls.get_by_key_name(guid)
        
    @classmethod
    def find_by_source(cls, source):
        return cls.all().filter("source =", source)
       
    def __repr__(self):
        return "%s(guid=%s, source=%s, body=%s)" % \
            (self.__class__.__name__, self.guid, self.source_name, self.body)