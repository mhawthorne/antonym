from unittest import main, TestCase

from katapult import numbers


class NumbersTest(TestCase):
    
    def test_safe_int_is_none(self):
        self.assertEquals(0, numbers.safe_int(None))


if __name__ == "__main__":
    main()