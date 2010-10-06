from unittest import main, TestCase

from antonym.ttwitter import TweetAnalyzer

from katapult.core import Record


class TweetAnalyzerTest(TestCase):
    
    def test_should_respond(self):
        analyzer = TweetAnalyzer()
        self.assert_(analyzer.should_respond(self.__msg("hi")), "should have responded")
        self.assertFalse(analyzer.should_respond(self.__msg("RT @livelock")), "should not have responded")

    def __msg(self, text):
        return Record(text=text)


if __name__ == "__main__":
    main()