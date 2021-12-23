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

import textwrap

from znoyder.lib import logger


LOG = logger.LOG


class ZnoyderCliException(Exception):
    '''Base Znoyder Cli Exception
    To use this class, inherit from it and define a
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.
    '''

    msg_fmt = 'An unknown exception occurred.'

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs
        self.message = message
        if not self.message:
            try:
                self.message = self.msg_fmt % kwargs
            except Exception:
                # arguments in kwargs doesn't match variables in msg_fmt
                import six
                for name, value in six.iteritems(kwargs):
                    LOG.error('%s: %s' % (name, value))
                self.message = self.msg_fmt


class PathError(ZnoyderCliException):
    def __init__(self, msg):
        super(self.__class__, self).__init__(msg)


class JobTypeError(ZnoyderCliException):
    def __init__(self, msg):
        super(self.__class__, self).__init__(msg)


class TriggerTypeError(ZnoyderCliException):
    def __init__(self, msg):
        super(self.__class__, self).__init__(msg)


class YAMLDuplicateKeyError(ZnoyderCliException):
    def __init__(self, key, node, context, start_mark):
        intro = textwrap.fill(textwrap.dedent('''\
        Zuul encountered a syntax error while parsing its configuration in the
        repo {repo} on branch {branch}.  The error was:'''.format(
            repo=context.project_name,
            branch=context.branch,
        )))

        e = textwrap.fill(textwrap.dedent('''\
        The key '{key}' appears more than once; duplicate keys are not
        permitted.
        '''.format(
            key=key,
        )))

        m = textwrap.dedent('''\
        {intro}
        {error}
        The error appears in the following stanza:
        {content}
        {start_mark}''')

        m = m.format(intro=intro,
                     error=indent(str(e)),
                     content=indent(start_mark.snippet.rstrip()),
                     start_mark=str(start_mark))
        super(self.__class__, self).__init__(m)


@staticmethod
def indent(s):
    return '\n'.join(['  ' + x for x in s.split('\n')])
