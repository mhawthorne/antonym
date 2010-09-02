from datetime import datetime
from unittest import TestLoader, TestSuite, TextTestRunner

def test_id(test_case):
    return "%s-%s" % (test_case.id(), timestamp())

def timestamp():
    """ generates a string timestamp, to second precision """
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def run_tests_from_classes(*test_classes):
    loader = TestLoader()
    suite = TestSuite((loader.loadTestsFromTestCase(tc) for tc in test_classes))
    TextTestRunner(verbosity=2).run(suite)