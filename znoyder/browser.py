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

from argparse import ArgumentParser
from pprint import PrettyPrinter
from urllib.parse import urlparse

from znoyder.distroinfo import get_distroinfo
from znoyder.package import Package


INFO_FILE = 'osp.yml'
RDOINFO_GIT_URL = 'https://code.engineering.redhat.com/gerrit/ospinfo'

APP_DESCRIPTION = 'Find OSP packages, repositories, components and releases.'


def get_components(**kwargs):
    info = get_distroinfo()
    components = info.get('components')

    if kwargs.get('name'):
        components = [component for component in components
                      if kwargs.get('name') == component.get('name')]

    return components


def get_projects_mapping(**kwawrgs) -> dict:
    packages = Package.get_osp_packages(**kwawrgs)
    projects_mapping = {}

    for package in packages:

        if package.upstream:
            upstream_name = urlparse(package.upstream).path[1:]
            upstream_name = upstream_name.replace("/", "-")
        else:
            upstream_name = package.name

        if package.osp_patches:
            projects_mapping[upstream_name] = urlparse(
                package.osp_patches).path[1:]
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


def extend_parser(parser) -> None:
    subparsers = parser.add_subparsers(dest='command', metavar='command')

    common = ArgumentParser(add_help=False)
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


def main(args) -> None:

    # TODO(abregman): to be removed after creating abstractions
    #                 for release and component
    default_output = []
    results = None

    if args.command == 'components':
        results = get_components(**vars(args))
        default_output = ['name']
    elif args.command == 'packages':
        packages = Package.get_osp_packages(**vars(args))
        packages = Package.filter(packages, vars(args))
    elif args.command == 'releases':
        results = get_releases(**vars(args))
        default_output = ['ospinfo_tag_name', 'git_release_branch']

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

    # TODO(abregman): to be removed after creating abstractions
    #                 for release and component
    if results:
        for result in results:
            print(' '.join([result.get(key, 'None') for key in output]))
    elif packages:
        for package in packages:
            print(package)


if __name__ == '__main__':
    main()
