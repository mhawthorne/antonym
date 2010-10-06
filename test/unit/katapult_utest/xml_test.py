from unittest import main, TestCase

from katapult.xml import unescape


class XmlTest(TestCase):
    
    def test_unescape_no_entities(self):
        s = "hi"
        self.assertEquals(s, unescape(s))

    def test_unescape_with_entities(self):
        self.assertEquals("<", unescape("&lt;"))
        self.assertEquals("abc", unescape("&#x61;&#98;&#x63;"))


if __name__ == "__main__":
    main()