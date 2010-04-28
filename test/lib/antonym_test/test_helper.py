from datetime import datetime


def test_id(test_case):
    return "%s-%s" % (test_case.id(), timestamp())

def timestamp():
    """ generates a string timestamp, to second precision """
    return datetime.now().strftime("%Y%m%d-%H%M%S")

