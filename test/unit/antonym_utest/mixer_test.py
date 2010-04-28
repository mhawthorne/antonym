import logging
import random
import unittest

import mox

from katapult.mocks import MockEntity, MockQuery

from antonym.accessors import ArtifactAccessor
from antonym.model import ArtifactContent, ArtifactSource, UrlResource
from antonym.mixer import Mixer


WORDS = ("pakistan", "a", "elephant", "is", "clowns", "at", "vampires")

def _phrase():
    return " ".join(random.sample(WORDS, 5))
    
def _create_content(count):
    source_name = "source-%s"
        
    return [MockEntity(key_name=str(count),
        source=MockEntity(key_name=source_name),
        source_name=source_name % count,
        body=_phrase()) for i in xrange(count)]


class MixerTest(unittest.TestCase):

    def test_mix_response(self):
        moxer = mox.Mox()
        moxer.StubOutWithMock(ArtifactAccessor, "search")
        
        inquiry = "how many elephants are in pakistan"
        
        # queries from longest word to shortest until target results are reached
        ArtifactAccessor.search("elephants").AndReturn(_create_content(5))
        ArtifactAccessor.search("pakistan").AndReturn(_create_content(5))
        
        moxer.ReplayAll()
        sources, text = Mixer.mix_response(inquiry)
        print text
        moxer.VerifyAll()

    def test_mix_response_no_search_results(self):
        moxer = mox.Mox()
        moxer.StubOutWithMock(ArtifactAccessor, "search")
        moxer.StubOutWithMock(Mixer, "random_resource")
        
        inquiry = "elephants"
        
        # no search results returned
        ArtifactAccessor.search("elephants").AndReturn(())
        Mixer.random_resource().AndReturn(MockEntity(key_name="failblog", url="http://failblog.org"))
        
        moxer.ReplayAll()
        sources, text = Mixer.mix_response(inquiry)
        print text
        moxer.VerifyAll()

    def test_mix_random_limit_sources_1(self):
        moxer = mox.Mox()
        
        moxer.StubOutWithMock(ArtifactSource, "all")
        moxer.StubOutWithMock(ArtifactContent, "all")
        
        def _source(id):
            return MockEntity(key_name=str(id), name="source/%d" % id)
        
        def _content(id):
            source = _source(0)
            return MockEntity(key_name=str(id), body="body for %d" % id, source=source, source_name=source.name)

        ArtifactSource.all().AndReturn(MockQuery(xrange(4), create_call=_source))
        ArtifactContent.all().AndReturn(MockQuery(xrange(12), create_call=_content))
        
        moxer.ReplayAll()
        sources, text = Mixer.mix_random_limit_sources(1)
        print "%s %s" % (";".join([s.name for s in sources]), text)
        self.assertEquals(len(sources), 1)
        moxer.VerifyAll()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()