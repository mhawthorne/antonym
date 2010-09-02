#!/usr/bin/env python2.6

from datetime import datetime
import sys
import urllib

from unittest import main, TestCase

import httplib2
import simplejson as json

from antonym_test.test_helper import run_tests_from_classes
from service_helper import PRIVATE_API_PREFIX, PUBLIC_API_PREFIX, assert_http_responses

from katapult.core import Hashes


class AbstractMixturesTest(TestCase):
    
    def setUp(self):
        if not host:
            self.fail("host must be provided.")
            
    def _base_url(self):
        self.fail("not implemented")
        
    def test_unauthorized(self):
        assert_http_responses(self, self._base_url(), ("DELETE", "HEAD", "GET", "POST", "PUT"), (401, 403, 405))


class PrivateMixturesTest(AbstractMixturesTest):
    
    def _base_url(self):
        return "%s%s/mixtures" % (host, PRIVATE_API_PREFIX)


class PublicMixturesTest(AbstractMixturesTest):
    
    def _base_url(self):
        return "%s%s/mixtures" % (host, PUBLIC_API_PREFIX)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.stderr.write("ERROR - expected <host>\n")
        sys.exit(1)

    host = sys.argv.pop(1)
    run_tests_from_classes(PrivateMixturesTest, PublicMixturesTest)
