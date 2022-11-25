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
from argparse import _SubParsersAction
from argparse import _UNRECOGNIZED_ARGS_ATTR
from argparse import SUPPRESS
from argparse import ArgumentError
import os

from znoyder import browser
from znoyder import downloader
from znoyder import finder
from znoyder import generator
from znoyder import templater
from znoyder.lib import logger


class OverridenSubparserAction(_SubParsersAction):
    """
        Modify the behavior of argparse's _SubParsersAction to avoid the
        override of arguments that are share between a parser and subparser.
    """
    def __init__(self, option_strings, prog, parser_class, dest=SUPPRESS,
                 required=False, help=None, metavar=None):

        self._prog_prefix = prog
        self._parser_class = parser_class
        self._name_parser_map = {}
        self._choices_actions = []

        super().__init__(option_strings=option_strings, prog=prog,
                         parser_class=parser_class, dest=dest,
                         help=help, metavar=metavar)
        self.required = required

    def _find_argument_option_strings(self, argument_dest, parser):
        for action in parser._actions:
            if action.dest == argument_dest:
                return action.option_strings

    def __call__(self, parser, namespace, values, option_string=None):
        parser_name = values[0]
        arg_strings = values[1:]

        # set the parser name if requested
        if self.dest is not SUPPRESS:
            setattr(namespace, self.dest, parser_name)

        # select the parser
        try:
            parser = self._name_parser_map[parser_name]
        except KeyError:
            args = {'parser': parser_name,
                    'choices': ', '.join(self._name_parser_map)}
            msg = 'unknown parser %(parser)r (choices: %(choices)s)' % args
            raise ArgumentError(self, msg)

        # parse all the remaining options into the namespace
        # store any unrecognized options on the object, so that the top
        # level parser can decide what to do with them

        # In case this subparser defines new defaults, we parse them
        # in a new namespace object and then update the original
        # namespace for the relevant parts.
        # We check whether the argument was actually specified or we
        # are using a default. If a default is being used in the subparser,
        # we keep the value already present in the namespace

        arg_strings_copy = arg_strings[:]
        subnamespace, arg_strings = parser.parse_known_args(arg_strings, None)
        for key, value in vars(subnamespace).items():
            if key in namespace:
                option_names = self._find_argument_option_strings(key, parser)
                was_passed_argument = [option in arg_strings_copy for option in
                                       option_names]
                if not any(was_passed_argument):
                    continue

            setattr(namespace, key, value)

        if arg_strings:
            vars(namespace).setdefault(_UNRECOGNIZED_ARGS_ATTR, [])
            getattr(namespace, _UNRECOGNIZED_ARGS_ATTR).extend(arg_strings)


def extend_parser_browser(parser) -> None:
    subparsers = parser.add_subparsers(dest='command', metavar='command')
    subparsers.required = True

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
    packages.add_argument('--osp-name', dest='osp_name')
    packages.add_argument('--osp-project', dest='osp_project')
    packages.add_argument('--project', dest='project')
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

    parser.add_argument('-p', '--pipeline',
                        dest='pipeline',
                        help='comma separated pipelines to return',
                        required=True)


def extend_parser_generator(parser) -> None:
    parser.add_argument('--component', dest='component',
                        help='OSP component name to filter projects')
    parser.add_argument('--name', dest='name',
                        help='package name to filter projects')
    parser.add_argument('--osp-name', dest='osp_name',
                        help='OSP package name to filter projects')
    parser.add_argument('--osp-project', dest='osp_project',
                        help='OSP project name to filter projects')
    parser.add_argument('--project', dest='project',
                        help='project name to filter projects')
    parser.add_argument('--tag', dest='tag',
                        help='OSP release tag to filter projects')


def extend_parser_templater(parser) -> None:
    pass


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
    # create a new parser with parameters that should be shared by all commands
    # through inheritance
    shared_parser = ArgumentParser(add_help=False)
    shared_parser.add_argument(
        '--log-mode',
        default="both",
        choices={"file", "terminal", "both"},
        help='Where to write the output, default is both'
    )
    shared_parser.add_argument(
        '-f', '--log-file',
        dest='log_file',
        default='znoyder_output.log',
        help='Path to store the output, default is znoyder_output.log'
    )

    parser = ArgumentParser(epilog='available commands:\n',
                            formatter_class=RawDescriptionHelpFormatter,
                            parents=[shared_parser])
    # subparsers will need to use a modified subparser action since the
    # argparse one would override the arguments from the main parser if they
    # were specified there but not in the subparser
    subparsers = parser.add_subparsers(action=OverridenSubparserAction)
    parser.add_argument('options', nargs=REMAINDER,
                        help='additional arguments to the selected command')

    for command_name, command_dict in COMMANDS.items():
        parser_command = subparsers.add_parser(command_name,
                                               parents=[shared_parser])
        parser_command.set_defaults(
            func=getattr(command_dict['module'], 'main'))
        parser.epilog += "  {}:  {}\n".format(
            command_name, command_dict['help'])
        command_dict['extend_parser_func'](parser_command)

    arguments = parser.parse_args(argv)
    return arguments


def main(argv=None) -> None:
    args = process_arguments(argv)
    logger.set_logger_destination(args)
    args.func(args)
