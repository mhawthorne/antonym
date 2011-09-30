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
"""WSGI middleware to measure the memory footprint of a GAE application."""

from instruments import Recorder
from google.appengine.api import capabilities
from google.appengine.api import lib_config

import logging
import os
import re
import sys


class Config(object):
    """Provides configuration constants.

    To override appstats configuration valuess, define values like this
    in your appengine_config.py file (in the root of your app):

        apptrace_URL_PATTERNS = ['^/$']
        apptrace_TRACE_MODULES = ['main.py']
    """
    
    URL_PATTERNS  = []
    TRACE_MODULES = []

    NAMESPACE     = '__apptrace__'
    INDEX_KEY     = 'apptrace_index'
    RECORD_PREFIX = 'apptrace_record'

    IGNORE_NAMES  = ['__builtins__', '__doc__', '__file__', '__loader__',
                     '__name__']
    IGNORE_TYPES  = ['module']

    def get_modules():
        """Returns plain module names without the file extension."""

        def _strip(mod):
            if mod.endswith('.py'):
                mod = mod[:-3]
            if os.sep in mod:
                mod = mod.replace(os.sep, '.')
            return mod

        return [_strip(module) for module in config.TRACE_MODULES]


config = lib_config.register('apptrace', Config.__dict__)


def apptrace_middleware(application):
    """WSGI middleware for measuring the memory footprint over requests.

    Args:
        application: A WSGIApplication instance.
    """
    server_software = os.environ.get('SERVER_SOFTWARE', '')

    if server_software.startswith('Dev'):
        # In order to allow access to the Guppy-PE package, we have to
        # circumvent some soft restrictions of the development appserver.
        from google.appengine.tools import dev_appserver

        ADD_WHITE_LIST_C_MODULES = [
            'heapyc',
            'setsc',
        ]

        ADD_WHITE_LIST_PARTIAL_MODULES = {
            'os': ['getpid'],
            'gc': ['get_objects'],
        }

        if 'os' in sys.modules: del sys.modules['os']
        if 'gc' in sys.modules: del sys.modules['gc']

        import_hook_class = dev_appserver.HardenedModulesHook

        import_hook_class._WHITE_LIST_C_MODULES.extend(ADD_WHITE_LIST_C_MODULES)

        for module in ADD_WHITE_LIST_PARTIAL_MODULES:
            import_hook_class._WHITE_LIST_PARTIAL_MODULES[module].extend(
                ADD_WHITE_LIST_PARTIAL_MODULES[module])

    compiled_url_patterns = [re.compile(p) for p in config.URL_PATTERNS]

    recorder = Recorder(config)

    def wsgi_app(environ, start_response):
        app = application(environ, start_response)
        if not capabilities.CapabilitySet('memcache').is_enabled():
            logging.error("Memcache service not available.")
            return app

        record = False
        path_info = os.environ['PATH_INFO']
        for re_obj in compiled_url_patterns:
            if re.match(re_obj, path_info):
                record = True
                break

        if record: recorder.trace()

        return app

    return wsgi_app
