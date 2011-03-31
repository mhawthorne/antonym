#!/usr/bin/env python

import logging
import sys
from StringIO import StringIO
from unittest import TestLoader, TestSuite, TextTestRunner


def fail(msg, code=1):
    sys.stderr.write("ERROR - %s\n" % msg)
    sys.exit(code)

if len(sys.argv) < 2:
    fail("expected <name1> [<name2> ... <nameN>]")

tests = []
loader = TestLoader()
for i, name in enumerate(sys.argv[1:]):
    # detects end of arguments
    if name == "-":
        del sys.argv[0:i]
        break
        
    print "loading tests from %s" % name
    __import__(name)
    tests.extend(loader.loadTestsFromName(name))

if not tests:
    fail("no tests found")

# debugging argv handling
print "sys.argv: %s" % sys.argv

logging.basicConfig(level=logging.DEBUG)

suite = TestSuite(tests)
TextTestRunner(verbosity=2).run(suite)