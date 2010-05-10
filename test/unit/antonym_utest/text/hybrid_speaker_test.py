from unittest import main, TestCase

import mox

from antonym.text.speakers import AbstractSpeaker, HybridSpeaker


class HybridSpeakerTest(TestCase):
    
    def test_ingests_for_multiple_speakers(self):
        moxer = mox.Mox()
        s1 = moxer.CreateMock(AbstractSpeaker)
        s2 = moxer.CreateMock(AbstractSpeaker)
        
        text = "hello"
        s1.ingest(text)
        s2.ingest(text)
        
        moxer.ReplayAll()
        speaker = HybridSpeaker(s1, s2)
        speaker.ingest(text)
        moxer.VerifyAll()
        
    def test_selects_from_first_speaker(self):
        moxer = mox.Mox()
        s1 = moxer.CreateMock(AbstractSpeaker)
        s2 = moxer.CreateMock(AbstractSpeaker)
        
        selected = ()
        s1.select(selected).AndReturn("hi")
        
        moxer.ReplayAll()
        speaker = HybridSpeaker(s1, s2)
        speaker.select(selected)
        moxer.VerifyAll()
        
    def test_selects_from_second_speaker(self):
        moxer = mox.Mox()
        s1 = moxer.CreateMock(AbstractSpeaker)
        s2 = moxer.CreateMock(AbstractSpeaker)
        
        selected = ()
        # s1.select() returns None, so s2.select() is called
        s1.select(selected)
        s2.select(selected).AndReturn("hi")
        
        moxer.ReplayAll()
        speaker = HybridSpeaker(s1, s2)
        speaker.select(selected)
        moxer.VerifyAll()


if __name__ == "__main__":
    main()