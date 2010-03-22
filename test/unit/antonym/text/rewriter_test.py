import re
import unittest

from antonym.text.rewriting import RegexRewriter


class RegexRewriterTest(unittest.TestCase):

    def test(self):
        text_name = 'mmattozzi'
        name_pattern = "mmattozzi"
        twitter_name = '@mikemattozzi'
        
        r = RegexRewriter({ name_pattern: twitter_name })
        
        # empty string unchanged
        self.assertEquals(r.rewrite(''), '')
        
        # name only string changed
        self.assertEquals(r.rewrite(text_name), twitter_name)
        
        # 1 rewrite
        self.assertEquals(r.rewrite("hello %s" % text_name), "hello %s" % twitter_name)
        
        # 2 rewrites
        self.assertEquals(r.rewrite("hello %s %s" % (text_name, text_name)), "hello %s %s" % (twitter_name, twitter_name))
        
        # no rewrite of non full word
        # src_text = "sonof%s" % text_name
        # self.assertEquals(r.rewrite(src_text), src_text)


if __name__ == '__main__':
    unittest.main()