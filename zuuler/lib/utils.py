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

from zuuler.lib.exceptions import PathError
from zuuler.lib import logger


LOG = logger.LOG

ZUUL_CONFIGS = ['zuul.yaml', '.zuul.yaml', 'zuul.d', '.zuul.d']
ZUUL_CONFIG_DIRS = ['zuul.d', '.zuul.d']


def get_config_paths(local_path) -> list:
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
        raise PathError('Provided path does not exists: %s' % local_path)

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
