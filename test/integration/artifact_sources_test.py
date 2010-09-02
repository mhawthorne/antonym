#!/usr/bin/env python2.6

from datetime import datetime
import sys
import urllib

from unittest import main, TestCase

import httplib2
import simplejson as json

from katapult.core import Hashes

from antonym_test.test_helper import run_tests_from_classes, test_id
from antonym_test.users import default_creds

from service_helper import PRIVATE_API_PREFIX, PUBLIC_API_PREFIX, \
    api_login_headers, assert_http_responses, assert_writes_forbidden, \
    create_put_wrapper, request_and_verify


class AbstractArtifactSourcesTest(TestCase):
    
    def setUp(self):
        if not host:
            self.fail("host must be provided.")
            
        self.base_url = self._base_url()
        self.test_id = test_id(self)
    
    def _base_url(self):
        self.fail("not implemented")
    
    def _request_headers(self):
        return {}

    def _request_keywords(self):
        return {}
  
    def test_unauthorized(self):
        assert_http_responses(self, self._base_url(), ("DELETE", "HEAD", "GET", "POST", "PUT"), (401, 403, 405))
          
    def test_get_nonexistent(self):
        url = self._test_url()
        request_and_verify(self, 404, url, "GET", headers=self._request_headers(),
            **self._request_keywords())
    
    def _test_url(self):
        return "%s/%s" % (self.base_url, self.test_id)

    def test_delete(self):
        url = self._test_url()
        create_put_wrapper(self, url, lambda url, **kw: None, headers=self._request_headers(),
            **self._request_keywords())
        
        # verifies that delete works
        request_and_verify(self, 404, url, "GET", headers=self._request_headers(),
            **self._request_keywords())

    def test_put(self):
        def op(url, **kw):
            response, content = request_and_verify(self, 200, url, "GET", **kw)
            feed_hash = json.loads(content)
            missing = Hashes.missing_fields(feed_hash, ("name", "count"))
            if missing:
                self.fail("missing fields: %s" % missing)
        
        url = self._test_url()    
        feed = self.__feed_hash()
        body = json.dumps(feed)
        create_put_wrapper(self, url, op, headers=self._request_headers(), body=body,
            **self._request_keywords())

    def __feed_hash(self):
        return dict(source="antonym/%s" % self.test_id,
            url="http://gilesbowkett.blogspot.com/feeds/posts/default",
            active=True)


class PrivateArtifactSourcesTest(AbstractArtifactSourcesTest):
    
    def _base_url(self):
        return "%s%s/sources" % (host, PRIVATE_API_PREFIX)

    def _request_headers(self):
        return api_login_headers()


class PublicArtifactSourcesTest(AbstractArtifactSourcesTest):
    
    def _base_url(self):
        return "%s%s/sources" % (host, PUBLIC_API_PREFIX)
        
    def _request_keywords(self):
        u, p = default_creds()
        return dict(user=u, passwd=p)

    # def test_writes(self):
    #     assert_writes_forbidden(self, self._test_url())


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("ERROR - expected <host>\n")
        sys.exit(1)

    host = sys.argv.pop(1)
    run_tests_from_classes(PrivateArtifactSourcesTest, PublicArtifactSourcesTest)
