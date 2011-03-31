from unittest import main, TestCase

from google.appengine.api import memcache
from google.appengine.ext import db

from mox import IsA, Mox

from antonym.accessors import ArtifactAccessor, ArtifactSourceAccessor, Counters, FeedAccessor
from antonym.core import ConflictingDataException, DuplicateDataException, IllegalArgumentException, NotFoundException
from antonym.model import ArtifactContent, ArtifactInfo, ArtifactSource

from antonym_test import test_helper
from katapult.mocks import MockEntity, MockKey, MockQuery


class ArtifactAccessorTest(TestCase):

    SOURCE_NAME = 'antonym.test'
    CONTENT_TYPE = 'text/plain'
    
    def setUp(self):
        self.moxer = Mox()
        self.test_id = test_helper.test_id(self)
        
    def tearDown(self):
        self.moxer.UnsetStubs()
        
    def __keywords(self):
        return dict(source=self.SOURCE_NAME,
            content_type=self.CONTENT_TYPE,
            body=self.test_id)
        
    def test_create_empty(self):
        try:
            ArtifactAccessor.create()
            self.fail("exception expected")
        except IllegalArgumentException, ex:
            pass

    def test_create_no_source_name(self):
        self.moxer.StubOutWithMock(ArtifactInfo, "all", use_mock_anything=True)
        
        self.moxer.ReplayAll()
        try:
            ArtifactAccessor.create(msg='hi')
            self.fail("exception expected.")
        except IllegalArgumentException:
            pass
        self.moxer.VerifyAll()

    def test_create_duplicate(self):
        self.moxer.StubOutWithMock(ArtifactInfo, "all", use_mock_anything=True)
        
        ArtifactInfo.all(keys_only=True).AndReturn(MockQuery(range(1), keys_only=True))
        
        self.moxer.ReplayAll()
        try:
            ArtifactAccessor.create(**self.__keywords())
            self.fail("exception expected")
        except DuplicateDataException, ex:
            pass
        self.moxer.VerifyAll()

    def test_create(self):
        accessor_save_kw = self.__keywords()
        source_name = accessor_save_kw['source']
        content_type = accessor_save_kw['content_type']
        body = accessor_save_kw['body']
        
        self.moxer.StubOutWithMock(ArtifactInfo, "all", use_mock_anything=True)
        self.moxer.StubOutWithMock(ArtifactSource, "get_or_create", use_mock_anything=True)
        self.moxer.StubOutWithMock(Counters, "source_counter", use_mock_anything=True)
        self.moxer.StubOutWithMock(ArtifactInfo, "create", use_mock_anything=True)
        self.moxer.StubOutWithMock(ArtifactContent, "create", use_mock_anything=True)
        
        source = MockEntity(key_name=source_name)
        ArtifactInfo.all(keys_only=True).AndReturn(MockQuery(None, keys_only=True))
        ArtifactSource.get_or_create(source_name).AndReturn(source)
        
        counter = self.moxer.CreateMockAnything()
        Counters.source_counter(source_name).AndReturn(counter)
        counter.increment()
        
        # TODO: I wish I could ignore keywords
        md5 = ArtifactAccessor._content_md5(source_name, content_type, body)
        info_save_kw = dict(source=source, source_name=source_name, content_type=content_type, content_md5=md5)
        info_key = MockKey(name=self.test_id)
        ArtifactInfo.create(**info_save_kw).AndReturn(info_key)
        
        content_save_kw = dict(source=source, source_name=source_name, info=info_key, body=body)
        ArtifactContent.create(info_key.name(), **content_save_kw).AndReturn(MockKey(name=self.test_id))
        
        self.moxer.ReplayAll()
        info, content, source = ArtifactAccessor.create(**accessor_save_kw)
        print 'info:%s, content:%s, source:%s' % (info, content, source)
        self.moxer.VerifyAll()

    def test_delete_nonexistent(self):
        self.moxer.StubOutWithMock(ArtifactInfo, "get_by_guid", use_mock_anything=True)
        self.moxer.StubOutWithMock(ArtifactContent, "get_by_guid", use_mock_anything=True)
        
        guid = 'blah'
        ArtifactInfo.get_by_guid(guid)
        ArtifactContent.get_by_guid(guid)
        
        self.moxer.ReplayAll()
        try:
            ArtifactAccessor.delete(guid)
            self.fail("exception expected")
        except NotFoundException, ex:
            pass
        self.moxer.VerifyAll()
        
    def _test_delete(self):
        self.moxer.StubOutWithMock(ArtifactInfo, "get_by_guid", use_mock_anything=True)
        self.moxer.StubOutWithMock(ArtifactContent, "get_by_guid", use_mock_anything=True)
        
        guid = 'blah'
        ArtifactInfo.get_by_guid(guid).AndReturn(MockEntity(MockKey(name=guid)))
        ArtifactContent.get_by_guid(guid).AndReturn(MockEntity(MockKey(name=guid)))
        
        self.moxer.ReplayAll()
        ArtifactAccessor.delete(guid)
        self.moxer.VerifyAll()


class ArtifactSourceAccessorTest(TestCase):
    
    def setUp(self):
        self.m = Mox()

    def test_delete_by_name_missing_source(self):
        self.m.StubOutWithMock(ArtifactSource, "get_by_name")
        
        name = "mhawthorne"
        ArtifactSource.get_by_name(name)
        
        self.m.ReplayAll()
        self.assertRaises(NotFoundException, ArtifactSourceAccessor.delete_by_name, name)
        self.m.VerifyAll()

    def test_delete_by_name_deletes_source_with_no_referencing_feed(self):
        self.m.StubOutWithMock(ArtifactSource, "get_by_name")
        self.m.StubOutWithMock(FeedAccessor, "get_by_source_name")
        self.m.StubOutWithMock(ArtifactInfo, "find_by_source")
        self.m.StubOutWithMock(ArtifactContent, "find_by_source")
        self.m.StubOutWithMock(db, "delete")
        self.m.StubOutWithMock(memcache, "delete")
        
        name = "mhawthorne"
        source = MockEntity(key_name=name)
        ArtifactSource.get_by_name(name).AndReturn(source)
        FeedAccessor.get_by_source_name(name, return_none=True)
        ArtifactInfo.find_by_source(source, keys_only=True).AndReturn(())
        ArtifactContent.find_by_source(source).AndReturn(())
        db.delete(source)
        memcache.delete(IsA(str)).AndReturn(1)
        
        self.m.ReplayAll()
        ArtifactSourceAccessor.delete_by_name(name)
        self.m.VerifyAll()

    def test_delete_by_name_deletes_source_with_referencing_feed(self):
        self.m.StubOutWithMock(ArtifactSource, "get_by_name")
        self.m.StubOutWithMock(FeedAccessor, "get_by_source_name")
        
        name = "mhawthorne"
        source = MockEntity(key_name=name)
        ArtifactSource.get_by_name(name).AndReturn(source)
        FeedAccessor.get_by_source_name(name, return_none=True).AndReturn(MockEntity(key=name, url="http://real.ly"))
        
        self.m.ReplayAll()
        self.assertRaises(ConflictingDataException, ArtifactSourceAccessor.delete_by_name, name)
        self.m.VerifyAll()


if __name__ == '__main__':
    main()