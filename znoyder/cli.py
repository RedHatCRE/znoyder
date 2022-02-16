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
    'browse-osp': {
        'help': 'explore ospinfo data to discover projects and releases',
        'module': browser
    },
    'download': {
        'help': 'fetch Zuul configuration files from repository',
        'module': downloader
    },
    'find-jobs': {
        'help': 'analyze Zuul configuration to find defined jobs',
        'module': finder
    },
    'templates': {
        'help': 'list defined jobs collection and remapping settings',
        'module': templater
    },
    'generate': {
        'help': 'create new Zuul configuration files for downstream testing',
        'module': generator
    }
}


def process_arguments(argv=None) -> Namespace:
    parser = ArgumentParser(epilog='available commands:\n',
                            formatter_class=RawDescriptionHelpFormatter,)
    subparsers = parser.add_subparsers()
    parser.add_argument('options', nargs=REMAINDER,
                        help='additional arguments to the selected command')

    for command_name, command_dict in COMMANDS.items():
        parser_command = subparsers.add_parser(command_name)
        parser_command.set_defaults(
            func=getattr(command_dict['module'], 'main'))
        parser.epilog += "  {}:  {}\n".format(
            command_name, command_dict['help'])
        getattr(command_dict['module'], 'extend_parser')(parser_command)

    arguments = parser.parse_args(argv)
    return arguments


def main(argv=None) -> None:
    args = process_arguments(argv)
    args.func(args)


if __name__ == '__main__':
    main()
