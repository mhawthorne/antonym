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
"""Unit tests for the apptrace WSGI middleware."""

import unittest


class TestMiddleware(unittest.TestCase):
    """Test case for WSGI middleware."""

    def test_import(self):
        """Importing the middleware."""

        import apptrace.middleware
        self.assertEqual('module', type(apptrace.middleware).__name__)

    def test_config(self):
        """Testing configuration."""

        from apptrace.middleware import config
        self.assertTrue(hasattr(config, 'URL_PATTERNS'))
        self.assertTrue(hasattr(config, 'TRACE_MODULES'))
        self.assertTrue(hasattr(config, 'NAMESPACE'))
        self.assertTrue(hasattr(config, 'INDEX_KEY'))
        self.assertTrue(hasattr(config, 'RECORD_PREFIX'))
        self.assertTrue(hasattr(config, 'IGNORE_NAMES'))
        self.assertTrue(hasattr(config, 'IGNORE_TYPES'))
