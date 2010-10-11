import re
from unittest import main, TestCase

import mox

from antonym.text.speakers.core import RandomSpeaker


class RandomSpeakerTest(TestCase):
    
    def test_ingest_and_speak(self):
        terms = sorted(set(re.split("\s+", open(__file__).read())))
        speaker = RandomSpeaker()
        speaker.ingest(" ".join(terms))
        speaker.compile()
        speaker.speak(1,len(terms) - 1)


if __name__ == "__main__":
    main()