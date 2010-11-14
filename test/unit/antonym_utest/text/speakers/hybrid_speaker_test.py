from unittest import main, TestCase

import mox

from antonym.text.speakers.core import SelectingSpeaker, HybridWordSpeaker


class HybridWordSpeakerTest(TestCase):
    
    def test_ingests_for_multiple_speakers(self):
        moxer = mox.Mox()
        s1 = moxer.CreateMock(SelectingSpeaker)
        s2 = moxer.CreateMock(SelectingSpeaker)
        
        text = "hello"
        s1.ingest(text)
        s2.ingest(text)
        
        moxer.ReplayAll()
        speaker = HybridWordSpeaker(s1, s2)
        speaker.ingest(text)
        moxer.VerifyAll()
        
    def test_selects_from_first_speaker(self):
        moxer = mox.Mox()
        s1 = moxer.CreateMock(SelectingSpeaker)
        s2 = moxer.CreateMock(SelectingSpeaker)
        
        selected = ()
        s1.select(selected, 1, 100).AndReturn("hi")
        
        moxer.ReplayAll()
        speaker = HybridWordSpeaker(s1, s2)
        speaker.select(selected, 1, 100)
        moxer.VerifyAll()
        
    def test_selects_from_second_speaker(self):
        moxer = mox.Mox()
        s1 = moxer.CreateMock(SelectingSpeaker)
        s2 = moxer.CreateMock(SelectingSpeaker)
        
        selected = ()
        # s1.select() returns None, so s2.select() is called
        s1.select(selected, 1, 100)
        s2.select(selected, 1, 100).AndReturn("hi")
        
        moxer.ReplayAll()
        speaker = HybridWordSpeaker(s1, s2)
        speaker.select(selected, 1, 100)
        moxer.VerifyAll()


if __name__ == "__main__":
    main()