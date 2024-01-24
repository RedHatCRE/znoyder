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
from znoyder.lib.utils import get_args_dict
from znoyder.lib.yaml import NoAliasDumper


LOG = logger.LOG


class FileCache(object):
    '''General-purpose persistent cache.'''

    def __init__(self, filename=None):
        self._cache = dict()
        self.filename = filename
        self.changed = False

        self.reload()

    def __call__(self, *keys, readable=False):
        def decorator(function):
            @wraps(function)
            def wrapper(*args, **kwargs):
                call_args = get_args_dict(function, args, kwargs)
                args_hash = ''

                if call_args:
                    if keys:  # filter out everything but wanted keys
                        for key in call_args.copy().keys():
                            if key not in keys:
                                del call_args[key]

                    if readable:
                        args_hash = str(list(call_args.values()))[1:-1]

                    else:
                        args_hash = hashlib.sha256(
                            pickle.dumps(call_args)
                        ).hexdigest()

                uuid = f'{function.__qualname__}({args_hash})'

                if uuid in self._cache:
                    return self._cache[uuid]

                else:
                    result = function(*args, **kwargs)
                    self._cache[uuid] = result
                    self.changed = True
                    return result

            return wrapper

        if len(keys) == 1 and callable(keys[0]):
            function, keys = keys[0], keys[1:]
            return decorator(function)
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
                sort_keys=True,
                width=math.inf,
            )
            file.write(data)
            file.write('\n')
