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

import argparse
from pprint import PrettyPrinter
import sys

from distroinfo import info as di


INFO_FILE = 'osp.yml'
RDOINFO_GIT_URL = 'https://code.engineering.redhat.com/gerrit/ospinfo'

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
    if kwargs.get('tag'):
        packages = [package for package in packages
                    if kwargs.get('tag') in package.get('tags')]
    if kwargs.get('upstream'):
        packages = [package for package in packages
                    if kwargs.get('upstream') in package.get('upstream')]

    return packages


def get_releases(**kwargs):
    info = get_distroinfo()
    releases = info.get('osp_releases')

    if kwargs.get('tag'):
        releases = [release for release in releases
                    if kwargs.get('tag') in release.get('ospinfo_tag_name')]

    return releases


def process_arguments():
    parser = argparse.ArgumentParser(description=APP_DESCRIPTION)
    subparsers = parser.add_subparsers(dest='command', metavar='command')

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--debug', dest='debug',
                        default=False, action='store_true',
                        help='print all fields in output')
    common.add_argument('--header', dest='header',
                        default=False, action='store_true',
                        help='print header with output names on top')
    common.add_argument('--output', dest='output',
                        help='comma-separated list of fields to return')

    components = subparsers.add_parser('components', help='', parents=[common])
    components.add_argument('--name', dest='name')

    packages = subparsers.add_parser('packages', help='', parents=[common])
    packages.add_argument('--component', dest='component')
    packages.add_argument('--name', dest='name')
    packages.add_argument('--tag', dest='tag')
    packages.add_argument('--upstream', dest='upstream')

    releases = subparsers.add_parser('releases', help='', parents=[common])
    releases.add_argument('--tag', dest='tag')

    arguments = parser.parse_args()

    if not arguments.command:
        parser.print_help()
        sys.exit(1)

    return arguments


def main():
    args = process_arguments()

    if args.command == 'components':
        results = get_components(**vars(args))
        default_output = ['name']
    elif args.command == 'packages':
        results = get_packages(**vars(args))
        default_output = ['osp-name', 'osp-distgit', 'osp-patches']
    elif args.command == 'releases':
        results = get_releases(**vars(args))
        default_output = ['ospinfo_tag_name', 'git_release_branch']
    else:
        results = None

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

    for result in results:
        print(' '.join([result.get(key, 'None') for key in output]))


if __name__ == '__main__':
    main()
