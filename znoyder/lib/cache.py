#!/usr/bin/env python3
#
# Copyright 2024 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

from functools import wraps
import hashlib
import math
import os
import pickle

import yaml

from znoyder.lib import logger
from znoyder.lib.yaml import NoAliasDumper


LOG = logger.LOG


class FileCache(object):
    '''General-purpose persistent cache.'''

    def __init__(self, filename=None):
        self._cache = dict()
        self.filename = filename
        self.changed = False

        self.reload()

    def __call__(self, arg=None):
        def decorator(function):
            @wraps(function)
            def wrapper(*args, **kwargs):
                key = function.__qualname__ + '(' + hashlib.sha256(
                    pickle.dumps(
                        (args, kwargs)
                    )
                ).hexdigest() + ')'

                if key in self._cache:
                    return self._cache[key]

                else:
                    result = function(*args, **kwargs)
                    self._cache[key] = result
                    self.changed = True
                    return result

            return wrapper

        if callable(arg):
            return decorator(arg)
        else:
            return decorator

    def __delitem__(self, key):
        del self._cache[key]

    def __getitem__(self, key):
        return self._cache[key]

    def __len__(self):
        return len(self._cache)

    def __setitem__(self, key, value):
        self._cache[key] = value

    def clear(self):
        self.changed = bool(self._cache)
        self._cache.clear()

    def reload(self):
        if self.filename and os.path.exists(self.filename):
            with open(self.filename, 'r') as file:
                self._cache = yaml.safe_load(file)
                self.changed = False

    def save(self):
        with open(self.filename, 'w') as file:
            data = '---\n' + yaml.dump(
                self._cache,
                Dumper=NoAliasDumper,
                default_flow_style=False,
                sort_keys=False,
                width=math.inf,
            )
            file.write(data)
            file.write('\n')
