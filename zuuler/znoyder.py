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


def process_arguments():
    parser = argparse.ArgumentParser(description=APP_DESCRIPTION)
    subparsers = parser.add_subparsers(dest='command', metavar='command')

    components = subparsers.add_parser('components', help='')
    components.add_argument('--name', dest='name')

    packages = subparsers.add_parser('packages', help='')
    packages.add_argument('--component', dest='component')
    packages.add_argument('--name', dest='name')
    packages.add_argument('--tag', dest='tag')
    packages.add_argument('--output', dest='output',
                          default='osp-name,osp-distgit,osp-patches',
                          help='comma-separated list of fields to return')
    packages.add_argument('--header', dest='header',
                          default=False, action='store_true',
                          help='print header with output names on top')
    packages.add_argument('--debug', dest='debug',
                          default=False, action='store_true',
                          help='print all fields in output')

    releases = subparsers.add_parser('releases', help='')
    releases.add_argument('--tag', dest='tag')
    releases.add_argument('--output', dest='output',
                          default='ospinfo_tag_name,git_release_branch',
                          help='comma-separated list of fields to return')
    releases.add_argument('--header', dest='header',
                          default=False, action='store_true',
                          help='print header with output names on top')
    releases.add_argument('--debug', dest='debug',
                          default=False, action='store_true',
                          help='print all fields in output')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    return args


def process_components(info, args):
    components = info.get('components')

    if args.name:
        components = [component for component in components
                      if args.name == component.get('name')]

    for component in components:
        print(component.get('name'))


def process_packages(info, args):
    packages = info.get('packages')

    packages = [package for package in packages
                if 'osp-name' in package.keys()]

    if args.component:
        packages = [package for package in packages
                    if args.component == package.get('component')]
    if args.name:
        packages = [package for package in packages
                    if args.name == package.get('name')]
    if args.tag:
        packages = [package for package in packages
                    if args.tag in package.get('tags')]

    if args.debug:
        pp = PrettyPrinter()
        pp.pprint(packages)
        return

    output = [entry.strip() for entry in args.output.split(',')]
    if args.header:
        print(' '.join(output))
        print(' '.join(['-' * len(field) for field in output]))

    for package in packages:
        print(' '.join([package.get(key, 'None') for key in output]))


def process_releases(info, args):
    releases = info.get('osp_releases')

    if args.tag:
        releases = [release for release in releases
                    if args.tag in release.get('ospinfo_tag_name')]

    if args.debug:
        pp = PrettyPrinter()
        pp.pprint(releases)
        return

    output = [entry.strip() for entry in args.output.split(',')]
    if args.header:
        print(' '.join(output))
        print(' '.join(['-' * len(field) for field in output]))

    for release in releases:
        print(' '.join([release.get(key, 'None') for key in output]))


def main():
    args = process_arguments()

    info = di.DistroInfo(info_files=INFO_FILE,
                         cache_ttl=24*60*60,  # 1 day in seconds
                         remote_git_info=RDOINFO_GIT_URL).get_info()

    if args.command == 'components':
        process_components(info, args)
    elif args.command == 'packages':
        process_packages(info, args)
    elif args.command == 'releases':
        process_releases(info, args)


if __name__ == '__main__':
    main()
