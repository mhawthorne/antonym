# -*- coding: utf-8 -*-
#
# Copyright 2010 Tobias Rodäbel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""User interface for interactive retrieval of apptrace records."""

from apptrace.middleware import config
from apptrace.instruments import Recorder
try:
    from django.utils import simplejson
except ImportError:
    import simplejson
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

import email
import google.appengine
import mimetypes
import os
import time


GAE_DIR = os.path.abspath(os.path.dirname(google.appengine.__file__))[:-17]


class StaticHandler(webapp.RequestHandler):
    """Request handler to serve static files."""

    def get(self):
        path = self.request.path
        filename = path[path.rfind('static/')+7:]
        filename = os.path.join(os.path.dirname(__file__), 'static', filename)
        content_type, encoding = mimetypes.guess_type(filename)
        try:
            assert content_type and '/' in content_type, repr(content_type)
            fp = open(filename, 'rb')
        except (IOError, AssertionError):
            self.response.set_status(404)
            return
        expiration = email.Utils.formatdate(time.time()+3600, usegmt=True)
        self.response.headers['Content-type'] = content_type
        self.response.headers['Cache-Control'] = 'public, max-age=expiry'
        self.response.headers['Expires'] = expiration
        try:
            self.response.out.write(fp.read())
        finally:
            fp.close()


class AJAXRecordsHandler(webapp.RequestHandler):
    """Serves JSON records."""

    def get(self):
        limit = int(self.request.GET.get('limit', 100))
        offset = int(self.request.GET.get('offset', 0))
        records = Recorder(config).get_raw_records(limit=limit, offset=offset)

        self.response.headers['Content-Type'] = 'application/octet-stream'
        self.response.out.write(records)


class BrowserHandler(webapp.RequestHandler):
    """Provides the code browser."""

    def get(self):
        filename = self.request.GET.get('filename')
        if filename.startswith('google_appengine'):
            filename = os.path.join(GAE_DIR, filename[17:])
        lineno = int(self.request.GET.get('lineno', 0))
        error = None
        code_lines = []
        try:
          fp = open(os.path.join('..', filename), 'r')
          code_lines = fp.readlines()
          fp.close()
        except IOError, e:
          error = u"File not found!"
          self.response.set_status(404)
        template_vars = {'app_id': os.environ['APPLICATION_ID'],
                         'filename': filename,
                         'lineno': lineno,
                         'error': error,
                         'code_lines': code_lines}
        self.response.out.write(template.render('code.html', template_vars))


class OverviewHandler(webapp.RequestHandler):
    """Serves the overview page."""

    def get(self):
        template_vars = {'app_id': os.environ['APPLICATION_ID'],
                         'records_url': '/_ah/apptrace/records'}
        self.response.out.write(template.render('index.html', template_vars))


def main():
    """The main function."""

    app = webapp.WSGIApplication([
        ('.*/static/.*', StaticHandler),
        ('.*/records.*', AJAXRecordsHandler),
        ('.*/browse.*', BrowserHandler),
        ('.*', OverviewHandler),
    ], debug=True)

    util.run_bare_wsgi_app(app)


if __name__ == "__main__":
    main()
