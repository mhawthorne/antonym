#!/usr/bin/env python2.6

from datetime import datetime
import sys
import urllib

from unittest import main, TestCase

import httplib2
import simplejson as json

from katapult.core import Hashes

from antonym_test.test_helper import test_id
from antonym_test import users
from service_helper import PRIVATE_API_PREFIX, api_login_headers, create_put_wrapper, request_and_verify


class FeedTest(TestCase):
    
    def setUp(self):
        if not host:
            self.fail("host must be provided.")
         
        self.host = host  
        self.base_feeds_url = "%s%s/feeds" % (host, PRIVATE_API_PREFIX)
        self.base_sources_url = "%s%s/sources" % (host, PRIVATE_API_PREFIX)
        self.test_id = test_id(self)
    
    def test_put_unauthorized(self):
        url = self.__feed_url(test_id(self))
        response, content = request_and_verify(self, 403, url, "PUT")
        
    def test_put_malformed_body(self):
        url = self.__feed_url(test_id(self))    
        request_and_verify(self, 400, url, "PUT", headers=api_login_headers(), body="hi")

    def test_put(self):
        def op(url, **kw):
            response, content = request_and_verify(self, 200, url, "GET", **kw)
            feed_hash = json.loads(content)
            missing = Hashes.missing_fields(feed_hash, ("url", "source", "active"))
            if missing:
                self.fail("missing fields: %s" % missing)
        
        url = self.__feed_url(test_id(self))
        source_name = self.test_id
        
        feed = self.__feed_hash()
        body = json.dumps(feed)
        headers = api_login_headers()
        
        try:
            create_put_wrapper(self, url, op, headers=headers, body=body)
        finally:
            # hack to delete source for feed
            request_and_verify(self, 204, "%s/%s" % (self.base_sources_url, source_name), "DELETE", headers=headers)
            
    def test_put_existing_source(self):
        source_name = test_id(self)
        source_url = "%s/%s" % (self.base_sources_url, source_name)
        
        def source_op(url, **kw):
            feed = self.__feed_hash()
            body = json.dumps(feed)
            feed_url = self.__feed_url(source_name)
            create_put_wrapper(self, feed_url, lambda url, **kw: True, body=body, **kw)
            
        create_put_wrapper(self, source_url, source_op, headers=api_login_headers())
        
    # this updates the existing record instead of creating a new one.  let it sit for a bit then delete the test.
    def _test_put_duplicate(self):
        feed = self.__feed_hash()
        request_body = json.dumps(feed)
        
        def op(url, **kw):
            # post content again
            request_and_verify(self, 409, url, "PUT", **kw)
        
        url = self.__feed_url(test_id(self))
        create_put_wrapper(self, url, op, headers=api_login_headers(), body=request_body)
        
    def test_get_nonexistent(self):
        url = self.__feed_url(test_id(self))
        request_and_verify(self, 404, url, "GET", headers=api_login_headers())
    
    def __feed_hash(self):
        return dict(#source="antonym/%s" % self.test_id,
            url="http://gilesbowkett.blogspot.com/feeds/posts/default",
            active=True)
    
    def __feed_url(self, source_name):
        return "%s/%s" % (self.base_feeds_url, source_name)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("ERROR - expected <host>\n")
        sys.exit(1)

    host = sys.argv.pop(1)
    main()
