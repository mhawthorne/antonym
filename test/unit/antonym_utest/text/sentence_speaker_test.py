from unittest import main, TestCase

from antonym.text.speakers import SentenceSpeaker


_text = """
Shamanism encompasses the belief that shamans are intermediaries or messengers between the human world and the spirit worlds.
Shamans are said to treat ailments/illness by mending the soul.
Alleviating traumas affecting the soul/spirit restores the physical body of the individual to balance and wholeness.
The shaman also enters supernatural realms or dimensions to obtain solutions to problems afflicting the community.
Shamans may visit other worlds/dimensions to bring guidance to misguided souls and to ameliorate illnesses of the human soul caused by foreign elements.
The shaman operates primarily within the spiritual world, which in turn affects the human world.
The restoration of balance results in the elimination of the ailment.
"""


class SentenceSpeakerTest(TestCase):

    def test(self):
        speaker = SentenceSpeaker()
        speaker.ingest(_text)
        for i in xrange(10):
            print "[%d] %s" % (i, speaker.speak(0, 130))


if __name__ == "__main__":
    main()