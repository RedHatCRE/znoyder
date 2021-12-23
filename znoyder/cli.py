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
from argparse import Namespace
from argparse import RawDescriptionHelpFormatter
from argparse import REMAINDER

from znoyder import browser
from znoyder import downloader
from znoyder import finder
from znoyder import generator
from znoyder import templater


COMMANDS = {
    'browse-osp': 'explore ospinfo data to discover projects and releases',
    'download': 'fetch Zuul configuration files from repository',
    'find-jobs': 'analyze Zuul configuration to find defined jobs',
    'templates': 'list defined jobs collection and remapping settings',
    'generate': 'create new Zuul configuration files for downstream testing',
}

COMMANDS_DESCRIPTION = '\n'.join([f'  {command:11s} {description}'
                                 for command, description in COMMANDS.items()])


def process_arguments(argv=None) -> Namespace:
    parser = ArgumentParser(
        epilog=f'available commands:\n{COMMANDS_DESCRIPTION}',
        formatter_class=RawDescriptionHelpFormatter,
    )

    parser.add_argument('command', metavar='command', choices=COMMANDS.keys(),
                        help='specify actual action to do')
    parser.add_argument('options', nargs=REMAINDER,
                        help='additional arguments to the selected command')

    arguments = parser.parse_args(argv)
    return arguments


def main(argv=None) -> None:
    args = process_arguments(argv)

    if args.command == 'browse-osp':
        browser.main(args.options)
    elif args.command == 'download':
        downloader.main(args.options)
    elif args.command == 'find-jobs':
        finder.main(args.options)
    elif args.command == 'templates':
        templater.main(args.options)
    elif args.command == 'generate':
        generator.main(args.options)


if __name__ == '__main__':
    main()
