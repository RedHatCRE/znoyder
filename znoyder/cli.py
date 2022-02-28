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

from argparse import ArgumentParser
from argparse import Namespace
from argparse import RawDescriptionHelpFormatter
from argparse import REMAINDER

from znoyder import browser
from znoyder import downloader
from znoyder import finder
from znoyder import generator
from znoyder import templater


def extend_parser_browser(parser) -> None:
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


def extend_parser_downloader(parser) -> None:
    parser.add_argument(
        '-r', '--repo', '--repository',
        dest='repository',
        help='repository to browse for files',
        metavar='REPOSITORY',
        required=True
    )
    parser.add_argument(
        '-b', '--branch',
        dest='branch',
        help='branch in repository to browse',
        metavar='BRANCH',
        required=True
    )
    parser.add_argument(
        '-d', '--destination',
        dest='destination',
        help='target directory for files to save',
        metavar='DESTINATION',
        required=True
    )
    parser.add_argument(
        '-n', '--non-fatal', '--errors-non-fatal',
        dest='errors_fatal',
        default=True,
        action='store_false',
        help='do not fail on non-existing remote'
    )
    parser.add_argument(
        '-s', '--skip', '--skip-existing',
        dest='skip_existing',
        default=False,
        action='store_true',
        help='do not overwrite existing files'
    )


def extend_parser_finder(parser) -> None:
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        default=os.environ.get('SHPERER_VERBOSE', False),
                        help='increase output verbosity [SHPERER_VERBOSE]')

    parser.add_argument('-d', '--dir',
                        dest='directory',
                        help='path to directory with zuul configuration',
                        required=True)

    parser.add_argument('-b', '--base',
                        dest='templates',
                        help='comma separated paths to jobs templates dirs',
                        required=True)

    parser.add_argument('-t', '--trigger',
                        dest='trigger',
                        help='comma separated job trigger types to return',
                        required=True)


def extend_parser_generator(parser) -> None:
    parser.add_argument(
        '-e', '--existing',
        dest='existing',
        default=True,
        action='store_false',
        help='use existing configs to generate jobs files (default)'
    )
    parser.add_argument(
        '-d', '--download',
        dest='download',
        default=False,
        action='store_true',
        help='download the zuul configuration files from repositories'
    )
    parser.add_argument(
        '-c', '--component',
        dest='component',
        help='OSP component name to filter projects'
    )
    parser.add_argument(
        '-n', '--name',
        dest='name',
        help='OSP package name to filter projects'
    )
    parser.add_argument(
        '--aggregate',
        dest='aggregate',
        help='File path where all templates will be aggregated'
    )
    parser.add_argument(
        '-t', '--tag',
        dest='tag',
        help='OSP release tag to filter projects'
    )
    parser.add_argument(
        '-g', '--generate',
        dest='generate',
        default=False,
        action='store_true',
        help='generate new zuul configuration files from upstream sources'
    )
    parser.add_argument(
        '-a', '--all', '--collect-all',
        dest='collect_all',
        default=False,
        action='store_true',
        help='collect all jobs when generating downstream configuration'
    )
    parser.add_argument(
        '-m', '--template-name',
        dest='template',
        default='zuul-project',
        help='Use defined template name, e.g. empty-zuul-project'
    )


def extend_parser_templater(parser) -> None:
    parser.add_argument(
        '-j', '--json',
        dest='json',
        default=False,
        action='store_true',
        help='produce output in JSON format'
    )


COMMANDS = {
    'browse-osp': {
        'help': 'explore ospinfo data to discover projects and releases',
        'module': browser,
        'extend_parser_func': extend_parser_browser
    },
    'download': {
        'help': 'fetch Zuul configuration files from repository',
        'module': downloader,
        'extend_parser_func': extend_parser_downloader
    },
    'find-jobs': {
        'help': 'analyze Zuul configuration to find defined jobs',
        'module': finder,
        'extend_parser_func': extend_parser_finder
    },
    'templates': {
        'help': 'list defined jobs collection and remapping settings',
        'module': templater,
        'extend_parser_func': extend_parser_templater
    },
    'generate': {
        'help': 'create new Zuul configuration files for downstream testing',
        'module': generator,
        'extend_parser_func': extend_parser_generator
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
        command_dict['extend_parser_func'](parser_command)

    arguments = parser.parse_args(argv)
    return arguments


def main(argv=None) -> None:
    args = process_arguments(argv)
    args.func(args)


if __name__ == '__main__':
    main()
