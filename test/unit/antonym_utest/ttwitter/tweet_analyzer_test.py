from unittest import main, TestCase

from antonym.ttwitter import TweetAnalyzer

from katapult.core import Record


class TweetAnalyzerTest(TestCase):
    
    def setUp(self):
        self.analyzer = TweetAnalyzer()
    
    def test_should_respond_returns_true_for_normal_message(self):
        self.assert_(self.analyzer.should_respond(self.__msg("hi")), "should have responded")
    
    def test_should_respond_returns_false_for_retweet_of_me(self):
        self.assertFalse(self.analyzer.should_respond(self.__msg("RT @livelock")), "should not have responded")

    def test_should_retweet_returns_true_for_normal_message(self):
        self.assert_(self.analyzer.should_retweet(self.__msg("hi")), "should have responded")

    def test_should_retweet_returns_false_for_retweet_of_me(self):
        self.assertFalse(self.analyzer.should_retweet(self.__msg("RT @livelock")), "should not have responded")

    def __retweet_of_me(self):
        self.__msg("RT @livelock something ridiculous and unintelligible")
        
    def __msg(self, text):
        return Record(text=text, user=Record(screen_name="mhawthorne"))


if __name__ == "__main__":
    main()