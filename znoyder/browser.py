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

import os.path

from pprint import PrettyPrinter
from urllib.parse import urlparse

from distroinfo import info as di


INFO_FILE = 'osp.yml'
RDOINFO_GIT_URL = 'https://github.com/redhat-openstack/rdoinfo.git'  # ospinfo

APP_DESCRIPTION = 'Find OSP packages, repositories, components and releases.'


def get_distroinfo():
    return di.DistroInfo(info_files=INFO_FILE,
                         cache_ttl=24*60*60,  # 1 day in seconds
                         remote_git_info=RDOINFO_GIT_URL).get_info()


def get_components(**kwargs):
    info = get_distroinfo()
    components = info.get('components')

    if kwargs.get('name'):
        components = [component for component in components
                      if kwargs.get('name') == component.get('name')]

    return components


def get_packages(**kwargs):
    info = get_distroinfo()
    packages = info.get('packages')

    packages = [package for package in packages
                if 'osp-name' in package.keys()]

    if kwargs.get('component'):
        packages = [package for package in packages
                    if kwargs.get('component') == package.get('component')]
    if kwargs.get('name'):
        packages = [package for package in packages
                    if kwargs.get('name') == package.get('name')]
    if kwargs.get('osp_name'):
        packages = [package for package in packages
                    if kwargs.get('osp_name') == package.get('osp-name')]
    if kwargs.get('project'):
        packages = [package for package in packages
                    if kwargs.get('project') == package.get('project')]
    if kwargs.get('tag'):
        packages = [package for package in packages
                    if kwargs.get('tag') in package.get('tags')]
    if kwargs.get('upstream'):
        packages = [package for package in packages
                    if kwargs.get('upstream') in str(package.get('upstream'))]

    for package in packages:
        repo_name = os.path.basename(package['osp-patches'])
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]  # drop the suffix
        package['osp-project'] = repo_name

    if kwargs.get('osp_project'):
        packages = [package for package in packages
                    if kwargs.get('osp_project') == package.get('osp-project')]

    return packages


def get_projects_mapping(**kwawrgs) -> dict:
    packages = get_packages(**kwawrgs)
    projects_mapping = {}

    for package in packages:

        if 'upstream' in package.keys() and package['upstream']:
            upstream_name = urlparse(package['upstream']).path[1:]
            upstream_name = upstream_name.replace("/", "-")
        else:
            upstream_name = package['name']

        if 'osp-patches' in package.keys() and package['osp-patches']:
            projects_mapping[upstream_name] = urlparse(
                package['osp-patches']).path[1:]
        else:
            projects_mapping[upstream_name] = upstream_name

    return projects_mapping


def get_releases(**kwargs):
    info = get_distroinfo()
    releases = info.get('osp_releases')

    if kwargs.get('tag'):
        releases = [release for release in releases
                    if kwargs.get('tag') in release.get('ospinfo_tag_name')]

    return releases


def main(args) -> None:
    if args.subcommand == 'components':
        results = get_components(**vars(args))
        default_output = ['name']
    elif args.subcommand == 'packages':
        results = get_packages(**vars(args))
        default_output = ['osp-name', 'osp-distgit', 'osp-patches']
    elif args.subcommand == 'releases':
        results = get_releases(**vars(args))
        default_output = ['ospinfo_tag_name', 'git_release_branch']
    else:
        results = None
        default_output = []

    if args.debug:
        pp = PrettyPrinter()
        pp.pprint(results)
        return

    if args.output:
        output = [entry.strip() for entry in args.output.split(',')]
    else:
        output = default_output

    if args.header:
        print(' '.join(output))
        print(' '.join(['-' * len(field) for field in output]))

    if results:
        for result in results:
            print(' '.join([str(result.get(key, 'None')) for key in output]))
