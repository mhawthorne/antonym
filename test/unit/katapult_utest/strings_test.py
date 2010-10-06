import logging
from unittest import main, TestCase

from katapult.strings import sanitize_encoding


class StringsTest(TestCase):
    
    def test_sanitize_encoding(self):
        u_str = u"\u2019"
        try:
             u_str.encode("ascii")
             self.fail("expected unicode-ascii error")
        except UnicodeEncodeError, e:
            pass
            
        # most common failure is logging-related
        logging.debug(sanitize_encoding(u_str))
        

if __name__ == "__main__":
    main()