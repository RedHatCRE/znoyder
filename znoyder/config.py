#!/usr/bin/env python3
#
# Copyright 2022 Red Hat, Inc.
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

import importlib.resources as pkg_resources

import yaml


with pkg_resources.open_text(__package__, 'config.yml') as file:
    CONFIG = yaml.load(file, Loader=yaml.FullLoader)

branches_map = CONFIG.get('branches', {})
include_map = CONFIG.get('include', {})
exclude_map = CONFIG.get('exclude', {})
add_map = CONFIG.get('add', {})
override_map = CONFIG.get('override', {})
copy_map = CONFIG.get('copy', {})

UPSTREAM_CONFIGS_DIR = 'jobs-upstream/'
GENERATED_CONFIGS_DIR = 'jobs-generated/'
GENERATED_CONFIG_PREFIX = 'cre-'
GENERATED_CONFIG_EXTENSION = '.yaml'
