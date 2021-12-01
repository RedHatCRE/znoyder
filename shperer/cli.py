#!/usr/bin/env python

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

import argparse
import datetime
import logging
import os
import sys

from shperer.lib import logger
from shperer.lib import zuul
from shperer.lib.exceptions import PathError

DESC = 'CLI to find ZUUL jobs, templates and associate them with projects'

LOG = logger.LOG


def as_list(item):
    if not item:
        return []
    if isinstance(item, list):
        return item
    return [item]


class ShpererShell(object):

    def get_base_parser(self) -> argparse.ArgumentParser:
        formatter = argparse.ArgumentDefaultsHelpFormatter

        parser = argparse.ArgumentParser(prog='shperer',
                                         description=DESC,
                                         formatter_class=formatter,
                                         add_help=False)

        parser.add_argument('-?', '-h', '--help',
                            action='help',
                            help='show this help message and exit')

        parser.add_argument('-v', '--verbose',
                            action='store_true',
                            default=os.environ.get('SHPERER_VERBOSE', False),
                            help='increase output verbosity [SHPERER_VERBOSE]')

        parser.add_argument('-d', '--dir',
                            help='project directory',
                            required=True)

        parser.add_argument('-b', '--base',
                            help='comma separated paths to base job '
                                 'template dirs',
                            required=True)

        parser.add_argument('-t', '--trigger',
                            help='comma separated job trigger types',
                            required=True)

        return parser

    def parse_args(self, argv) -> argparse.ArgumentParser:
        parser = self.get_base_parser()
        args = parser.parse_args(argv)

        if args.verbose:
            LOG.setLevel(level=logging.DEBUG)
            LOG.debug('Shperer running in debug mode')

        return args

    def main(self, argv):
        parser_args = self.parse_args(argv)
        LOG.debug("%s" % parser_args)
        LOG.debug('Project dir: %s' % parser_args.dir)
        LOG.debug('Template dirs: %s' % parser_args.base)
        LOG.debug('Trigger types: %s' % parser_args.trigger)

        trigger_types = []
        for trigger in parser_args.trigger.split(','):
            trigger_types.append(zuul.JobTriggerType.to_type(trigger))

        zuul_templates = []

        for template_dir in parser_args.base.split(','):
            project = zuul.ZuulProject(project_path=template_dir)
            templates = project.get_list_of_defined_templates(trigger_types)
            zuul_templates.extend(templates)

        project = zuul.ZuulProject(project_path=parser_args.dir,
                                   templates=zuul_templates)

        zuul_jobs = project.get_list_of_jobs(trigger_types)

        for job in zuul_jobs:
            print("%s: %s" % (job.job_trigger_type, job))

        project_templates = project.get_list_of_used_templates()
        for template in project_templates:
            for job in template.get_jobs(trigger_types):
                print("%s: %s in template %s" %
                      (job.job_trigger_type, job, template))


def main(args=None):

    start_time = datetime.datetime.now()

    try:
        if args is None:
            args = sys.argv[1:]

        ShpererShell().main(args)
    except PathError as ex:
        LOG.error(ex.message)
        sys.exit(1)
    finally:
        finish_time = datetime.datetime.now()
        LOG.debug('Finished shperer: %s' %
                  finish_time.strftime('%Y-%m-%d %H:%M:%S'))
        LOG.debug('Run time: %s [H]:[M]:[S].[ms]' %
                  str(finish_time - start_time))


if __name__ == "__main__":
    main()
