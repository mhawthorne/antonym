import re


class ParsedTweet:
    """
    attributes:
        full_text
        usernames
        hashtags
        plain_text
        plain_words
    """

    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)


USER_REGEX = re.compile("(?:@(\w+))")
def parse_tweet(tweet):
    plain_text = USER_REGEX.sub('', tweet).strip()
    plain_words = plain_text.split()
    
    usernames = []
    for u in USER_REGEX.findall(tweet):
        usernames.append(u)

    return ParsedTweet(plain_text=plain_text,
        plain_words=plain_words,
        usernames=usernames)