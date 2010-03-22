#!/usr/bin/env python2.6

from datetime import datetime
import sys
import urllib

from unittest import main, TestCase

import httplib2
import simplejson as json

from antonym_test import helper

from katapult.core import Hashes


class CronTwitterMixTest(TestCase):
    
    def setUp(self):
        if not host:
            self.fail("host must be provided.")
            
        self.base_url = "%s/cron/twitter/mix" % host
            
    def test_get(self):
        url = "%s?test=1" % self.base_url
        response, content = helper.request_and_verify(self, 200, url, "GET", headers=self.__login_headers())
        response_hash = json.loads(content)
        if not response_hash.has_key("test"):
            self.fail("unexpected JSON response: %s" % response_hash)
        
    def __login_headers(self):
        return helper.local_login_headers(admin=True)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.stderr.write("ERROR - expected <host>\n")
        sys.exit(1)

    host = sys.argv.pop(1)
    main()