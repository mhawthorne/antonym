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
"""Instruments for measuring the memory footprint of a GAE application."""

import os
import re
import sys
sys.path.insert(0, os.path.dirname(__file__))

try:
    from django.utils import simplejson
except ImportError:
    import simplejson

from google.appengine.api import memcache
from guppy import hpy

import gc
import inspect
import logging


class JSONSerializable(object):
    """Base class for JSON serializable objects."""

    def __setattr__(self, attr, value):
        self.__dict__['_k_'+attr] = value

    def __getattr__(self, attr):
        return self.__dict__['_k_'+attr]

    def __repr__(self):
        data = dict([(k[3:], self.get_value(self.__dict__[k]))
                     for k in self.__dict__ if k.startswith('_k_')])
        return unicode(data)

    @classmethod
    def get_value(C, value):
        return value

    @classmethod
    def make_value(C, value):
        return value

    def EncodeJSON(self):
        """Encodes record to JSON."""

        return simplejson.dumps(eval(repr(self)))

    @staticmethod
    def make_args(args):
        return dict([(str(k), args[k]) for k in args])

    @classmethod
    def FromJSON(C, json):
        """Deserializes JSON and returns a new instance of the given class.

        Args:
            C: This class.
            json: String containing JSON.
        """

        data = simplejson.loads(json)
        return C(**dict([(str(k), C.make_value(data[k])) for k in data]))


class RecordEntry(JSONSerializable):
    """Represents a single record entry."""

    def __init__(self,
                 module_name,
                 name,
                 obj_type,
                 dominated_size,
                 filename,
                 lineno):
        """Constructor.

        Args:
            module_name: Name of the module.
            name: The object name (key in module.__dict__).
            obj_type: String representing the type of the recorded object.
            dominated_size: Total size of memory that will become deallocated.
            filename: File path relative to the application root directory.
            lineno: Line number from where the corresponding code starts.
        """
        self.module_name = module_name
        self.name = name
        self.obj_type = obj_type
        self.dominated_size = dominated_size
        self.filename = filename
        self.lineno = lineno

    def __cmp__(self, other):
        if self.obj_type != other.obj_type:
            raise TypeError("Cannot compare entries for different types")
        return cmp(self.dominated_size, other.dominated_size)


class Record(JSONSerializable):
    """Represents a record.

    Records contain record entries.
    """

    def __init__(self, index, entries):
        """Constructor.

        Args:
            index: Integer.
            entries: List of RecordEntry instances.
        """
        self.index = index
        self.entries = entries

    @classmethod
    def get_value(C, value):
        if isinstance(value, list):
            new = []
            for item in value:
                if isinstance(item, RecordEntry):
                    new.append(eval(repr(item)))
                else:
                    new.append(item)
            value = new
        return value

    @classmethod
    def make_value(C, value):
        value = value
        if isinstance(value, list):
            new = []
            for item in value:
                new.append(RecordEntry(**super(Record, C).make_args(item)))
            value = new
        return value


class Recorder(object):
    """Traces the memory usage of various appllication modules."""

    def __init__(self, config):
        """Constructor.

        Args:
            config: A middleware.Config instance.
        """
        self._config = config

    @property
    def config(self):
        return self._config

    def trace(self):
        """Records momory data.

        Uses Heapy to retrieve information about allocated memory.
        """

        gc.collect()
        hp = hpy()

        # We use memcache to store records and take a straightforward
        # approach with a very simple index which is basically a counter.
        index = 1
        if not memcache.add(key=self.config.INDEX_KEY,
                            namespace=self.config.NAMESPACE,
                            value=index):
            index = memcache.incr(key=self.config.INDEX_KEY,
                                  namespace=self.config.NAMESPACE)

        record = Record(index, [])

        for name in self.config.get_modules():
            if name not in sys.modules:
                logging.warn('Unknown module "%s"', name)
                continue
            module = sys.modules[name]
            module_dict = module.__dict__
            keys = sorted(set(module_dict.keys())-set(self.config.IGNORE_NAMES))
            for key in keys:
                obj = module_dict[key]
                if hasattr(obj, '__class__'):
                    obj_type = obj.__class__.__name__
                else:
                    obj_type = str(obj).split('.')[-1]
                    logging.warn("Old style class '%s' detected", obj_type)

                if obj_type in self.config.IGNORE_TYPES:
                    continue

                iso = hp.iso(obj)

                try:
                    _, lineno = inspect.getsourcelines(obj)
                    fn = inspect.getsourcefile(obj)
                except (TypeError, IOError):
                    lines, lineno = inspect.getsourcelines(module)
                    for line in lines:
                        lineno += 1
                        if line.startswith(key):
                            break
                    fn = inspect.getsourcefile(module)

                fname = fn[len(list(os.path.commonprefix([fn, os.getcwd()]))):]
                fname = re.sub('^/', '', fname)

                entry = RecordEntry(
                    name, key, obj_type, iso.domisize, fname, lineno)

                record.entries.append(entry)

        # Store JSON records
        key = self.config.RECORD_PREFIX + str(index)
        memcache.add(key=key,
                     namespace=self.config.NAMESPACE,
                     value=record.EncodeJSON())

    def get_raw_records(self, limit=100, offset=0, join=True):
        """Returns raw records beginning with the latest.

        Args:
            limit: Max number of records.
            offset: Offset within overall results.
            join: If True return all records in one JSON string. Otherwise,
                return a list of JSON reocords.
        """

        curr_index = memcache.get(self.config.INDEX_KEY,
                                  namespace=self.config.NAMESPACE)
        if not curr_index:
            return '[]'

        if offset+1 > curr_index: offset = curr_index-1
        if limit > curr_index: limit = curr_index-offset 

        keys = [str(i+1) for i in xrange(offset, offset+limit)]

        result = memcache.get_multi(keys=keys,
                                    namespace=self.config.NAMESPACE,
                                    key_prefix=self.config.RECORD_PREFIX)

        records = [result[key] for key in keys]

        if join:
            return '['+', '.join(records)+']'
        return records

    def get_records(self, limit=100, offset=0):
        """Get stored records.

        Args:
            limit: Max number of records.
            offset: Offset within overall results.

        Returns lists of Record instances.
        """
        records = self.get_raw_records(limit=limit, offset=offset, join=False)
        return [Record.FromJSON(record) for record in records]
