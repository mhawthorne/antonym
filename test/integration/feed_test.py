#!/usr/bin/env python2.6

from datetime import datetime
import sys
import urllib

from unittest import main, TestCase

import httplib2
import simplejson as json

from antonym_test import helper, users

from katapult.core import Hashes


class FeedTest(TestCase):
    
    def setUp(self):
        if not host:
            self.fail("host must be provided.")
            
        self.base_url = "%s/api/feeds" % host
        self.test_id = helper.test_id(self)
    
    def test_put_unauthorized(self):
        url = self.__test_url()
        response, content = helper.request_and_verify(self, 403, url, "PUT")
        
    def test_put_malformed_body(self):
        url = self.__test_url()    
        helper.request_and_verify(self, 400, url, "PUT", headers=helper.api_login_headers(), body="hi")

    def test_put(self):
        def op(url, **kw):
            response, content = helper.request_and_verify(self, 200, url, "GET", **kw)
            feed_hash = json.loads(content)
            missing = Hashes.missing_fields(feed_hash, ("url", "source", "active"))
            if missing:
                self.fail("missing fields: %s" % missing)
        
        url = self.__test_url()    
        feed = self.__feed_hash()
        body = json.dumps(feed)
        helper.create_put_wrapper(self, url, op, headers=helper.api_login_headers(), body=body)
    
    # this updates the existing record instead of creating a new one.  let it sit for a bit then delete the test.
    def _test_put_duplicate(self):
        feed = self.__feed_hash()
        request_body = json.dumps(feed)
        
        def op(url, **kw):
            # post content again
            helper.request_and_verify(self, 409, url, "PUT", **kw)
        
        url = self.__test_url()    
        helper.create_put_wrapper(self, url, op, headers=helper.api_login_headers(), body=request_body)
        
    def test_get_nonexistent(self):
        url = self.__test_url()
        helper.request_and_verify(self, 404, url, "GET", headers=helper.api_login_headers())
    
    def __feed_hash(self):
        return dict(source="antonym/%s" % self.test_id,
            url="http://gilesbowkett.blogspot.com/feeds/posts/default",
            active=True)
    
    def __test_url(self):
        return "%s/%s" % (self.base_url, self.test_id)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("ERROR - expected <host>\n")
        sys.exit(1)

    host = sys.argv.pop(1)
    main()
