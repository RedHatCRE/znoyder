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
from argparse import ArgumentDefaultsHelpFormatter
import datetime
import logging
import os
import sys

from znoyder.lib import logger
from znoyder.lib import zuul
from znoyder.lib.exceptions import PathError


APP_DESCRIPTION = 'Find ZUUL jobs, templates and associate them with projects.'

LOG = logger.LOG


def find_jobs(directory, templates, triggers):
    LOG.debug('Directory: %s' % directory)

    project = zuul.ZuulProject(project_path=directory,
                               templates=templates)

    zuul_jobs = project.get_list_of_jobs(triggers)

    project_templates = project.get_list_of_used_templates()
    for template in project_templates:
        zuul_jobs.extend(template.get_jobs(triggers))

    return zuul_jobs


def find_templates(directories, triggers):
    LOG.debug('Directories: %s' % directories)

    zuul_templates = []

    for directory in directories.split(','):
        project = zuul.ZuulProject(project_path=directory)
        templates = project.get_list_of_defined_templates(triggers)
        zuul_templates.extend(templates)

    return zuul_templates


def find_triggers(triggers):
    LOG.debug('Triggers: %s' % triggers)

    trigger_types = []

    for trigger in triggers.split(','):
        trigger_types.append(zuul.JobTriggerType.to_type(trigger))

    return trigger_types


def _cli_find_jobs(directory, templates, triggers):
    LOG.debug('Project dir: %s' % directory)
    LOG.debug('Template dirs: %s' % templates)
    LOG.debug('Trigger types: %s' % triggers)

    trigger_types = []
    for trigger in triggers.split(','):
        trigger_types.append(zuul.JobTriggerType.to_type(trigger))

    zuul_templates = []

    for template_dir in templates.split(','):
        project = zuul.ZuulProject(project_path=template_dir)
        templates = project.get_list_of_defined_templates(trigger_types)
        zuul_templates.extend(templates)

    project = zuul.ZuulProject(project_path=directory,
                               templates=zuul_templates)

    zuul_jobs = project.get_list_of_jobs(trigger_types)

    for job in zuul_jobs:
        print('%s: %s' % (job.job_trigger_type, job))

    project_templates = project.get_list_of_used_templates()
    for template in project_templates:
        for job in template.get_jobs(trigger_types):
            print('%s: %s in template %s' %
                  (job.job_trigger_type, job, template))


def extend_parser(parser) -> None:
    formatter = ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(prog='shperer',
                            description=APP_DESCRIPTION,
                            formatter_class=formatter, add_help=False)

    parser.add_argument('-?', '-h', '--help',
                        action='help',
                        help='show this help message and exit')

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


def main(args) -> None:
    if args.verbose:
        LOG.setLevel(level=logging.DEBUG)
        LOG.debug('Shperer CLI running in debug mode')

    LOG.debug('%s' % args)

    start_time = datetime.datetime.now()

    try:
        _cli_find_jobs(args.directory,
                       args.templates,
                       args.trigger)

    except PathError as ex:
        LOG.error(ex.message)
        sys.exit(1)

    finally:
        finish_time = datetime.datetime.now()
        LOG.debug('Finished shperer: %s' %
                  finish_time.strftime('%Y-%m-%d %H:%M:%S'))
        LOG.debug('Run time: %s [H]:[M]:[S].[ms]' %
                  str(finish_time - start_time))


if __name__ == '__main__':
    main()
