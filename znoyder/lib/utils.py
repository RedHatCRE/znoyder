#!/usr/bin/env python3
#
# Copyright 2021 Red Hat, Inc.
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

import os
import re

from znoyder.lib.exceptions import PathError
from znoyder.lib import logger


LOG = logger.LOG

ZUUL_CONFIGS = ['zuul.yaml', '.zuul.yaml', 'zuul.d', '.zuul.d']
ZUUL_CONFIG_DIRS = ['zuul.d', '.zuul.d']


def drop_nones_from_dict(collection: dict) -> dict:
    '''Deletes keys from dictionary in place where values are set to None.

    Parameters
    ----------
    collection : dict
        The dictionary to process.

    Returns
    -------
    collection : dict
        The input dictionary without any key that had value set to None.

    Examples
    --------
    >>> drop_nones_from_dict({'a': 1, 'b': 2, 'c': None})
    {'a': 1, 'b': 2}
    >>> drop_nones_from_dict({'a': 1, 'b': {'c': 2, 'd': None}})
    {'a': 1, 'b': {'c': 2}}
    '''

    for key, value in collection.copy().items():
        if isinstance(collection[key], dict):
            drop_nones_from_dict(collection[key])
        elif value is None:
            del collection[key]

    return collection


def get_config_paths(local_path: str) -> list:
    '''Returns the list of all absolute paths to zuul configuration
       files from the given project directory

    Raises:
        PathError: If there was error for a given local_path

    Args:
        local_path (:obj:`str`): absolute path to the project directory

    Returns:
        (:obj:`list`): paths to zuul configuration files
    '''

    LOG.debug('Finding zuul config files in: %s' % local_path)

    zuul_config_files = []

    if not os.path.exists(local_path):
        raise PathError('Provided path does not exist: %s' % local_path)

    if not os.access(local_path, os.R_OK):
        raise PathError('Provided path is not readable: %s' % local_path)

    if not os.path.isdir(local_path):
        raise PathError('Provided path is not directory: %s' % local_path)

    zuul_file_regex = re.compile('|'.join(ZUUL_CONFIGS))

    for root, subdirs, files in os.walk(local_path):
        # Get the list of all config files from zuul config dir
        for zuul_config_dir in ZUUL_CONFIG_DIRS:
            if root.endswith(zuul_config_dir):
                for walk_file in files:
                    zuul_config_files.append(os.path.join(root, walk_file))

        # Get the individual zuul config files
        for walk_file in files:
            if zuul_file_regex.match(walk_file):
                zuul_config_files.append(os.path.join(root, walk_file))

    LOG.debug('Using zuul config files: %s' % zuul_config_files)

    if not zuul_config_files:
        LOG.warning('No zuul config files found in: %s' % local_path)

    return zuul_config_files


def get_args_dict(fn, args, kwargs):
    # by https://stackoverflow.com/a/40363565
    args_names = fn.__code__.co_varnames[:fn.__code__.co_argcount]
    return {**dict(zip(args_names, args)), **kwargs}


def match(string: str, specifier: str) -> bool:
    '''Function checks if a given string is matched by a given specifier.

    The match is performed in the awk-inspired fashion:
    – if the specifier starts and ends with the forward slash (/), e.g. /foo/,
      then the content between slashes is treated as regular expression,
    – otherwise it is a value that should fully match the input string.

    Parameters
    ----------
    string : str
        The string that should be tested against specifier.
    specifier : str
        The expected value or regular expression to be matched against.

    Returns
    -------
    matched : bool
        True if given string matches the specifier, False otherwise.

    Examples
    --------
    >>> match('foobar', 'foobar')
    True
    >>> match('foobar', 'foo')
    False
    >>> match('foobar', '/foo/')
    True
    '''

    if specifier.startswith('/') and specifier.endswith('/'):
        regex = re.compile(specifier[1:-2])
        return bool(regex.search(string))
    else:
        regex = re.compile(specifier)
        return bool(regex.fullmatch(string))


def merge_dicts(a: dict, b: dict, path=None, override=False) -> dict:
    '''Merges dict `b` into dict `a` in place and also returns updated `a`.

    Inspired by https://stackoverflow.com/a/7205107

    Parameters
    ----------
    a : dict
        The first dictionary, the one that should be updated.
    b : str
        The second dictionary, that shall be merged into the first one.

    Returns
    -------
    a : dict
        The first dict after being merged with second dict.

    Examples
    --------
    >>> merge_dicts({'a': 1, 'b': 2}, {'b': 2})
    {'a': 1, 'b': 2}
    >>> merge_dicts({'a': 1, 'b': {'c': 2}}, {'b': {'d': 3}})
    {'a': 1, 'b': {'c': 2, 'd': 3}}
    >>> merge_dicts({'a': 1, 'b': {'c': 2}}, {'b': {'c': 3}})
    Traceback (most recent call last):
     ...
    Exception: Conflict at path: b.c
    '''

    if path is None:
        path = []

    if b:
        for key in b:
            if a and key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    merge_dicts(a[key], b[key], path + [str(key)], override)
                elif a[key] == b[key]:
                    pass
                elif not a[key] and b[key] or override:
                    a[key] = b[key]
                else:
                    path = '.'.join(path + [str(key)])
                    raise Exception(f'Conflict at path: {path}')
            else:
                a[key] = b[key]

    return a


def sort_dict_by_keys(collection: dict) -> dict:
    '''Nested sort of the dictionary elements in place by keys.

    Parameters
    ----------
    collection : dict
        The dictionary to process.

    Returns
    -------
    collection : dict
        The sorted dictionary.

    Examples
    --------
    >>> sort_dict_by_keys({'b': 1, 'a': 4, 'c': 3})
    {'a': 4, 'b': 1, 'c': 3}
    >>> sort_dict_by_keys({'b': {'g': 6, 'e': 7, 'f': 5}, 'a': 4, 'c': 3})
    {'a': 4, 'b': {'e': 7, 'f': 5, 'g': 6}, 'c': 3}
    '''

    data = collection.copy()
    collection.clear()

    collection.update(dict(sorted(data.items())))

    for key, value in collection.copy().items():
        if isinstance(collection[key], dict):
            sort_dict_by_keys(collection[key])

    return collection
