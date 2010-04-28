#!/usr/bin/env python2.6

from datetime import datetime
import sys
import urllib

from unittest import main, TestCase

import httplib2
import simplejson as json

from katapult.core import Hashes

from antonym_test import test_helper, users

import service_helper


class ArtifactSourcesTest(TestCase):
    
    def setUp(self):
        if not host:
            self.fail("host must be provided.")
            
        self.base_url = "%s/api/sources" % host
        self.test_id = test_helper.test_id(self)
    
    def test_put_unauthorized(self):
        url = self.__test_url()
        response, content = service_helper.request_and_verify(self, 403, url, "PUT")

    def test_put(self):
        def op(url, **kw):
            response, content = service_helper.request_and_verify(self, 200, url, "GET", **kw)
            feed_hash = json.loads(content)
            missing = Hashes.missing_fields(feed_hash, ("name", "count"))
            if missing:
                self.fail("missing fields: %s" % missing)
        
        url = self.__test_url()    
        feed = self.__feed_hash()
        body = json.dumps(feed)
        service_helper.create_put_wrapper(self, url, op, headers=service_helper.api_login_headers(), body=body)
    
    # this updates the existing record instead of creating a new one.  let it sit for a bit then delete the test.
    def _test_put_duplicate(self):
        feed = self.__feed_hash()
        request_body = json.dumps(feed)
        
        def op(url, **kw):
            # post content again
            service_helper.request_and_verify(self, 409, url, "PUT", **kw)
        
        url = self.__test_url()    
        service_helper.create_put_wrapper(self, url, op, headers=service_helper.api_login_headers(), body=request_body)
        
    def test_get_nonexistent(self):
        url = self.__test_url()
        service_helper.request_and_verify(self, 404, url, "GET", headers=service_helper.api_login_headers())

    def test_delete(self):
        url = self.__test_url()    
        service_helper.create_put_wrapper(self, url, lambda url, **kw: None, headers=service_helper.api_login_headers())
        
        # verifies that delete works
        service_helper.request_and_verify(self, 404, url, "GET", headers=service_helper.api_login_headers())

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
