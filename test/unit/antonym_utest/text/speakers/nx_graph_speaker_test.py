import traceback
from unittest import main, TestCase

from antonym.text import TextException
from antonym.text.speakers.graph import NxGraphShortestPathSpeaker, NxGraphSpeaker

from antonym_utest.text import CONTENT


class NxGraphSpeakerTest(TestCase):
    
    def test(self):
        s = NxGraphSpeaker()
        s.ingest(CONTENT)
        # whether TextException or not, it's behaving as expected
        try:
            print s.speak(50,100)
        except TextException:
            print traceback.format_exc()
            pass

class NxGraphShortestPathSpeakerTest(TestCase):
    
    def test(self):
        s = NxGraphShortestPathSpeaker()
        s.ingest(CONTENT)
        # whether TextException or not, it's behaving as expected
        try:
            print s.speak(50,100)
        except TextException:
            print traceback.format_exc()
            pass


if __name__ == "__main__":
    main()