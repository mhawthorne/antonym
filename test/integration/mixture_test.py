#!/usr/bin/env python2.6

from datetime import datetime
import sys
import urllib

from unittest import main, TestCase

import httplib2
import simplejson as json

from antonym_test import helper

from katapult.core import Hashes


class MixtureTest(TestCase):
    
    def setUp(self):
        if not host:
            self.fail("host must be provided.")
            
        self.base_url = "%s/api/mixture" % host
    
    def test_get_unauthorized(self):
        url = self.base_url
        helper.request_and_verify(self, 403, url, "GET")
        
    def test_get(self):
        url = self.base_url
        response, content = helper.request_and_verify(self, 200, url, "GET", headers=self.__login_headers())
        mixture_hash = json.loads(content)
        missing = Hashes.missing_fields(mixture_hash, ('sources', 'body'))
        if missing:
            self.fail("missing fields: %s" % missing)
            
    def __login_headers(self):
        return helper.api_login_headers()


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.stderr.write("ERROR - expected <host>\n")
        sys.exit(1)

    host = sys.argv.pop(1)
    main()