#!/usr/bin/env python2.6

from datetime import datetime
import sys
import urllib

from unittest import main, TestCase, TestLoader, TestSuite, TextTestRunner

import httplib2
import simplejson as json

from katapult.core import Hashes, NotImplementedException

from antonym_test.test_helper import run_tests_from_classes, test_id
from antonym_test.users import default_creds

from service_helper import PRIVATE_API_PREFIX, PUBLIC_API_PREFIX, api_login_headers, assert_writes_forbidden, request_and_verify


_source = 'antonym.test'

def _create_artifact_wrapper(test_case, base_url, source_url, operation, **kw):
    """
    handles artifact creation and deletion.
    
    params:
        operation - a method that is inject with the URL of a new artifact.
    """
    response, content = request_and_verify(test_case, 204, base_url, "POST", **kw)
    try:
        location_key = "location"
        if not location_key in response:
            test_case.fail("header '%s' not found in response" % location_key)
        artifact_url = response[location_key]
    
        operation(artifact_url, **kw)
    finally:
        request_and_verify(test_case, 204, artifact_url, "DELETE", **kw)
        request_and_verify(test_case, 204, source_url, "DELETE", **kw)


class AbstractArtifactTest(TestCase):
    
    def setUp(self):
        if not host:
            self.fail("host must be provided.")
    
        self.base_url = self._artifact_url()
        self.source_url = self._source_url(_source)
        
        # self.base_url = "%s/api/artifacts" % host
        # self.source_url = "%s/api/sources/%s" % (host, _source)

    def _artifact_url(self):
        raise NotImplementedException()
    
    def _source_url(self, source):
        raise NotImplementedException()
        
    def _login_headers(self):
        return {}
        
    def _request_keywords(self):
        return {}

    def _build_artifact_url(self):
        return "%s/%s" % (self.base_url, test_id(self))

    def __artifact_hash(self):
        return {'source': _source,
            'content-type': 'text/plain',
            'body': test_id(self) }
        
    def test_get_nonexistent(self):
        url = self._build_artifact_url()
        request_and_verify(self, 404, url, "GET", headers=self._login_headers(),
            **self._request_keywords())

    def test_post(self):
        def _op(url, **kw):
            response, content = request_and_verify(self, 200, url, "GET", **kw)
            artifact_hash = json.loads(content)
            missing = Hashes.missing_fields(artifact_hash, ('guid', 'source', 'content-type', 'modified', 'modified-by', 'body'))
            if missing:
                self.fail("missing artifact fields: %s" % missing)
            
        body = json.dumps(self.__artifact_hash())
        _create_artifact_wrapper(self, self.base_url, self.source_url, _op, headers=self._login_headers(),
            body=body, **self._request_keywords())

    def test_delete(self):
        url_ref = []
        keywords = {}
        def _op(url, **kw):
            url_ref.append(url)
            keywords.update(kw)
            
        body = json.dumps(self.__artifact_hash())
        _create_artifact_wrapper(self, self.base_url, self.source_url, _op, headers=self._login_headers(),
            body=body, **self._request_keywords())
        
        # verify deletion
        url = url_ref.pop()
        request_and_verify(self, 404, url, "GET", **keywords)
        
        
class PrivateArtifactTest(AbstractArtifactTest):

    def _artifact_url(self):
        return "%s%s/artifacts" % (host, PRIVATE_API_PREFIX)

    def _source_url(self, source):
        return "%s%s/sources/%s" % (host, PRIVATE_API_PREFIX, source)
    
    def _login_headers(self):
        return api_login_headers()

    def test_post_duplicate(self):
        artifact = {'source': _source,
            'content-type': 'text/plain',
            'body': test_id(self) }
        request_body = json.dumps(artifact)

        def _op(url, **kw):
            # post content again
            request_and_verify(self, 409, self.base_url, "POST", **kw)
        
        _create_artifact_wrapper(self, self.base_url, self.source_url, _op, headers=self._login_headers(), 
            body=request_body, **self._request_keywords())

    def test_post_unauthorized(self):
        url = self._build_artifact_url()
        response, content = request_and_verify(self, (401, 403), self.base_url, "POST")
        
    def test_post_malformed_body(self):
        request_and_verify(self, 400, self.base_url, "POST", headers=self._login_headers(),
            body="hi", **self._request_keywords())


class PublicArtifactTest(AbstractArtifactTest):    
    
    def _artifact_url(self):
        return "%s%s/artifacts" % (host, PUBLIC_API_PREFIX)
        
    def _source_url(self, source):
        return "%s%s/sources/%s" % (host, PUBLIC_API_PREFIX, source)
        
    def _request_keywords(self):
        u, p = default_creds()
        return dict(user=u, passwd=p)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("ERROR - expected <host>\n")
        sys.exit(1)

    host = sys.argv.pop(1)
    run_tests_from_classes(PrivateArtifactTest, PublicArtifactTest)
