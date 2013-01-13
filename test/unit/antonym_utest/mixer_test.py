import logging
import random
import re
import unittest

import mox

from katapult.log import basic_config
from katapult.mocks import MockEntity, MockQuery

from antonym.accessors import ArtifactAccessor
from antonym.model import ArtifactContent, ArtifactSource, UrlResource
from antonym.mixer import Mixer
from antonym.text.speakers.core import PhraseSpeaker

from antonym_utest.text import generate_phrase, create_content_list


def new_default_mixer():
    # return Mixer.new(new_speaker()[1])
    return Mixer(PhraseSpeaker())

def _inject(word, phrase):
    """ injects a word into a phrase """
    words = phrase.split()
    words.append(word)
    random.shuffle(words)
    return " ".join(words)

def _source(id):
    return MockEntity(key_name=str(id), name="source/%d" % id)

def _content(id, length=8):
    source = _source(0)
    id_str = str(id)
    return MockEntity(key_name=id_str, guid=id_str, body=generate_phrase(length), source=source, source_name=source.name)


class MixerTest(unittest.TestCase):

    def test_mix_response(self):
        moxer = mox.Mox()
        moxer.StubOutWithMock(ArtifactAccessor, "search")
        
        inquiry = "how many elephants are in pakistan during winter"
        
        # queries from longest word to shortest until target results are reached
        ArtifactAccessor.search("elephants").AndReturn(create_content_list(5))
        ArtifactAccessor.search("pakistan").AndReturn(create_content_list(5))
        
        moxer.ReplayAll()
        sources, text = new_default_mixer().mix_response(inquiry)
        print text
        moxer.VerifyAll()

    def __default_mix_results(self):
        return (), "hello"
        
    def test_mix_response_no_search_results(self):
        m = mox.Mox()
        m.StubOutWithMock(ArtifactAccessor, "search")
        # m.StubOutWithMock(Mixer, "random_resource")
        m.StubOutWithMock(Mixer, "mix_random_limit_sources")
        
        inquiry = "elephants"
        
        # no search results returned
        ArtifactAccessor.search("elephants").AndReturn(())
        Mixer.mix_random_limit_sources(1).AndReturn(self.__default_mix_results())
        # Mixer.random_resource().AndReturn(MockEntity(key_name="failblog", url="http://failblog.org"))
        
        m.ReplayAll()
        sources, text = new_default_mixer().mix_response(inquiry)
        m.VerifyAll()

    def test_mix_response_mix_contents_fails(self):
        m = mox.Mox()
        m.StubOutWithMock(ArtifactAccessor, "search")
        # m.StubOutWithMock(Mixer, "random_resource")
        m.StubOutWithMock(Mixer, "mix_random_limit_sources")
        
        inquiry = "elephants"
        
        # content should be short enough to make SentenceSpeaker fail
        ArtifactAccessor.search("elephants").AndReturn(tuple(e for e in MockQuery(xrange(1), create_call=lambda id: _content(id, 0))))
        Mixer.mix_random_limit_sources(1).AndReturn(self.__default_mix_results())
        #Mixer.random_resource().AndReturn(MockEntity(key_name="failblog", url="http://failblog.org"))
        
        m.ReplayAll()
        sources, text = new_default_mixer().mix_response(inquiry)
        m.VerifyAll()
        
    def test_mix_random_limit_sources_1(self):
        moxer = mox.Mox()
        
        moxer.StubOutWithMock(ArtifactSource, "all")
        moxer.StubOutWithMock(ArtifactContent, "all")

        ArtifactSource.all().AndReturn(MockQuery(xrange(4), create_call=_source))
        ArtifactContent.all().AndReturn(MockQuery(xrange(12), create_call=_content))
        
        moxer.ReplayAll()
        sources, text = new_default_mixer().mix_random_limit_sources(1)
        self.assertEquals(len(sources), 1)
        moxer.VerifyAll()

    def test_mix_sources_1(self):
        moxer = mox.Mox()
        
        moxer.StubOutWithMock(ArtifactSource, "get_multiple_by_name")
        moxer.StubOutWithMock(ArtifactContent, "all")

        source_name = "source/1"
        source = MockEntity(key_name=source_name, name=source_name)
        
        def _content(id):
            id_str = str(id)
            return MockEntity(key_name=id_str, guid=id_str, body=generate_phrase(5), source=source, source_name=source.name)
        
        ArtifactSource.get_multiple_by_name(source_name).AndReturn((source, ))
        ArtifactContent.all().AndReturn(MockQuery(xrange(12), create_call=_content))
        
        moxer.ReplayAll()
        sources, text = new_default_mixer().mix_sources(source_name)
        self.assertEquals(len(sources), 1)
        moxer.VerifyAll()

    def test_mix_sources_2(self):
        moxer = mox.Mox()
        
        moxer.StubOutWithMock(ArtifactSource, "get_multiple_by_name")
        moxer.StubOutWithMock(ArtifactContent, "all")

        source_names = ("source/1", "source/2")
        sources = [MockEntity(key_name=name, name=name) for name in source_names]
        
        def _content(id):
            # toggles between sources
            source = sources[id % 2]
            id_str = str(id)
            return MockEntity(key_name=id_str, guid=id_str, body=generate_phrase(5), source=source, source_name=source.name)
        
        ArtifactSource.get_multiple_by_name(source_names).AndReturn(sources)
        
        # performs ArtifactContent query for each source
        ArtifactContent.all().AndReturn(MockQuery(xrange(12), create_call=_content))
        ArtifactContent.all().AndReturn(MockQuery(xrange(12), create_call=_content))
        
        moxer.ReplayAll()
        mixed_sources, text = new_default_mixer().mix_sources(source_names)
        self.assertEquals(len(mixed_sources), len(source_names))
        moxer.VerifyAll()
        
    def test_blacklist(self):
        # all of these words should be replaced
        blacklist_words = ('cim', '#cim', 'CIM', '#CIM', 'cimdata', 'CIMData',
            'comcast', '#comcast', 'Comcast', '#Comcast',
            'comcast.net', 
            'fancast', 'Fancast', 'fancast.com',
            'xfinity', 'Xfinity', 'xfinity.com',
            'thePlatform', 'theplatform', 'platform', 'the platform',
            'streamsage', 'StreamSage',
            'xcal', 'excalibur', 'Excalibur', 'ccp', 'CCP',
            'mhorwitz', 'mhorwtiz', 'horwitz', 'bad dog', 'Bad Dog',
            'jason press', 'Jason Press', 'jpress',
            'amy banse', 'sam schwartz', 'bruce',
            'mansnimar', 'arkady',
            'https://www.yammer.com/theplatform.com/nickrossi',
            'tp', 'tP', 'Tp', 'TP',
            # relax, I'm half black
            'nigger', 'NIGGER', 'Nigger', 'nigga', 'NIGGA', 'Nigga')
        
        # these corner-case words should remain untouched
        # 'footprint' should not be replaced, even thought it contains 'tp', which should be replaced
        untouched_words = ('http://superbad.com', 'footprint')
        
        def _source(id):
            return MockEntity(key_name=str(id), name="source/%d" % id)
        
        def _content(include_word):
            source = _source(0)
            return MockEntity(key_name=include_word, guid=include_word, body=_inject(include_word , generate_phrase(5)), source=source, source_name=source.name)

        # #no should be surrounded by spaces or the start/end of text
        replace_word = "#hi"
        black_replacement_regex = re.compile(r'^%s\s|\s%s$|\s%s\s' % tuple([replace_word for i in xrange(3)]))
        
        # TODO: reduce duplication
        def test_words(words, text_call):
            for i in xrange(len(words)):
                moxer = mox.Mox()
        
                moxer.StubOutWithMock(ArtifactSource, "all")
                moxer.StubOutWithMock(ArtifactContent, "all")

                ArtifactSource.all().AndReturn(MockQuery(xrange(4), create_call=_source))
            
                word = words[i]
                source_content = _content(word) 
                source_text = source_content.body
                ArtifactContent.all().AndReturn(MockQuery(xrange(1), create_call=lambda id: source_content))
        
                moxer.ReplayAll()
                mixer = new_default_mixer()
                sources, mixed_text = mixer.mix_random_limit_sources(1)
                print "('%s') '%s' -> '%s'" % (word, source_text, mixed_text)
                text_call(word, source_text, mixed_text)
                moxer.VerifyAll()

        def blacklist_call(word, source_text, mixed_text):
            self.assertFalse(word in mixed_text, "'%s' contains '%s'; should not" % (mixed_text, word))
            self.assert_(black_replacement_regex.search(mixed_text), "%s -> %s" % (source_text, mixed_text))

        test_words(blacklist_words, blacklist_call)
        
        def untouched_call(word, source_text, mixed_text):
            self.assertEquals(source_text, mixed_text)

        test_words(untouched_words, untouched_call)


if __name__ == '__main__':    
    basic_config()
    unittest.main()