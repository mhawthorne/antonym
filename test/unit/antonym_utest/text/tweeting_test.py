import re
import unittest

from antonym.text.tweeting import parse_tweet


class TweetParsingTest(unittest.TestCase):

    def test_no_users(self):
        tweet = "why is blood spattered all over the car?"
        result = parse_tweet(tweet)
        self.assertEquals(tweet, result.plain_text)
        self.assertEquals(tweet.split(), result.plain_words)
    
    def test_single_user(self):
        tweet = "@livelock why is blood spattered all over the car?"
        plain_text = "why is blood spattered all over the car?"
        users = ["livelock"]
        
        result = parse_tweet(tweet)
        self.assertEquals(plain_text, result.plain_text)
        self.assertEquals(plain_text.split(), result.plain_words)
        self.assertEquals(result.usernames, users)

    def test_multiple_users(self):
        tweet = "@livelock why is blood spattered all over @mhawthorne's car?"
        plain_text = "why is blood spattered all over 's car?"
        users = ["livelock", "mhawthorne"]
        
        result = parse_tweet(tweet)
        self.assertEquals(plain_text, result.plain_text)
        self.assertEquals(plain_text.split(), result.plain_words)
        self.assertEquals(result.usernames, users)

if __name__ == '__main__':
    unittest.main()