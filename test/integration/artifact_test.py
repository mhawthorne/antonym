#!/usr/bin/env python2.6

from datetime import datetime
import sys
import urllib

from unittest import main, TestCase

import httplib2
import simplejson as json

from antonym_test import helper

from katapult.core import Hashes


def _create_artifact_wrapper(test_case, base_url, operation, **kw):
    """
    handles artifact creation and deletion.
    
    params:
        operation - a method that is inject with the URL of a new artifact.
    """
    response, content = helper.request_and_verify(test_case, 204, base_url, "POST", **kw)
    try:
        location_key = "location"
        if not location_key in response:
            test_case.fail("header '%s' not found in response" % location_key)
        artifact_url = response[location_key]
    
        operation(artifact_url, **kw)
    finally:
        # TODO: test deletes
        helper.request(artifact_url, "DELETE", **kw)


class ArtifactTest(TestCase):
    
    def setUp(self):
        if not host:
            self.fail("host must be provided.")
            
        self.base_url = "%s/api/artifacts" % host
    
    def test_post_unauthorized(self):
        url = self.__artifact_url()
        response, content = helper.request_and_verify(self, 403, self.base_url, "POST")
        
    def test_post_malformed_body(self):
        helper.request_and_verify(self, 400, self.base_url, "POST", headers=helper.api_login_headers(), body="hi")

    def test_post(self):
        def op(url, **kw):
            response, content = helper.request_and_verify(self, 200, url, "GET", **kw)
            artifact_hash = json.loads(content)
            missing = Hashes.missing_fields(artifact_hash, ('guid', 'source', 'content-type', 'modified', 'modified-by', 'body'))
            if missing:
                self.fail("missing artifact fields: %s" % missing)
            
        artifact = {'source': 'antonym.test',
            'content-type': 'text/plain',
            'body': helper.test_id(self) }
        body = json.dumps(artifact)
        _create_artifact_wrapper(self, self.base_url, op, headers=helper.api_login_headers(), body=body)
    
    def test_post_duplicate(self):
        artifact = {'source': 'antonym.test',
            'content-type': 'text/plain',
            'body': helper.test_id(self) }
        request_body = json.dumps(artifact)
        
        def op(url, **kw):
            # post content again
            helper.request_and_verify(self, 409, self.base_url, "POST", **kw)
        
        _create_artifact_wrapper(self, self.base_url, op, headers=helper.api_login_headers(), body=request_body)
        
    def test_get_nonexistent(self):
        url = self.__artifact_url()
        helper.request_and_verify(self, 404, url, "GET", headers=helper.api_login_headers())
        
        
    def __artifact_url(self):
        return "%s/%s" % (self.base_url, helper.test_id(self))


class BulkArtifactTest(TestCase):

    def setUp(self):
        if not host:
            self.fail("host must be provided.")
            
        self.base_url = "%s/api/artifacts2" % host

    def __artifact_url(self):
        return "%s/%s" % (self.base_url, helper.test_id(self))

    def test_post_unauthorized(self):
        helper.request_and_verify(self, 401, self.base_url, "POST")

    def test_post(self):
        def op(url, **kw):
            response, content = helper.request_and_verify(self, 200, url, "GET", **kw)
            artifact_hash = json.loads(content)
            missing = Hashes.missing_fields(artifact_hash, ('guid', 'source', 'content-type', 'modified', 'modified-by', 'body'))
            if missing:
                self.fail("missing artifact fields: %s" % missing)
            
        artifact = {'source': 'antonym.test',
            'content-type': 'text/plain',
            'body': helper.test_id(self) }
        body = json.dumps(artifact)
        _create_artifact_wrapper(self, self.base_url, op, body=body, user='', passwd='')


class ArtifactSearchTest(TestCase):
    
    def _test_search(self):
        response, content = helper.request_and_verify(self, 200, url, "GET", **kw)
        result_hash = json.loads(content)
        result_count = len(result_hash)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("ERROR - expected <host>\n")
        sys.exit(1)

    host = sys.argv.pop(1)
    main()