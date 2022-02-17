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
from urllib.parse import urlparse

from znoyder.distroinfo import get_distroinfo


class Package():

    def __init__(self, name, tags, component=None, upstream=None, **kwargs):
        self.name = name
        self.tags = tags
        self.component = component
        self.upstream = upstream
        self.osp_project = urlparse(kwargs.get('osp-patches')).path[1:]
        self.osp_name = kwargs.get('osp-name')
        self.osp_distgit = kwargs.get('osp-distgit')
        self.osp_patches = kwargs.get('osp-patches')

    @staticmethod
    def filter(packages, filters):
        if filters.get('component'):
            packages = [package for package in packages
                        if filters.get('component') == package.component]
        if filters.get('name'):
            packages = [package for package in packages
                        if filters.get('name') == package.name]
        if filters.get('tag'):
            packages = [package for package in packages
                        if filters.get('tag') in package.tags]
        if filters.get('upstream'):
            packages = [package for package in packages
                        if filters.get('upstream') in str(package.upstream)]
        return packages

    def __str__(self):
        return str(self.osp_name)

    @staticmethod
    def get_osp_packages(**kwargs):
        info = get_distroinfo()
        packages = info.get('packages')

        packages = [Package(**package) for package in packages
                    if 'osp-name' in package.keys()]

        return packages
