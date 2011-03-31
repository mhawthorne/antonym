import sys
from unittest import main, TestCase

from mox import Mox

from katapult import strings


class Text(unicode):
    """ unicode subclass.  appengine's Text type extends unicode and is causing errors, so I want to test this case """
    pass


class StringsTest(TestCase):
    
    _string_with_unicode_char = "\xc2"
    
    def test_sanitize_encoding_handles_string_with_unicode_char(self):
        strings.sanitize_encoding(self._string_with_unicode_char)

    def test_sanitize_encoding_handles_unicode_with_unicode_char(self):
        strings.sanitize_encoding(u"\xc2")

    def test_sanitize_encoding_handles_string_with_unicode_exception(self):
        m = Mox()
        m.StubOutWithMock(strings, '_unicode')
        try:
            strings._unicode(self._string_with_unicode_char, "utf8", "replace").AndRaise(TypeError("testing"))
            m.ReplayAll()
        
            strings.sanitize_encoding(self._string_with_unicode_char)
            self.fail("exception expected")
        except TypeError, e:
            pass
        finally:
            m.UnsetStubs()
            
        m.VerifyAll()

    def test_sanitize_encoding_handles_unicode_subclass(self):
        strings.sanitize_encoding(Text("hi"))
        
if __name__ == "__main__":
    main()