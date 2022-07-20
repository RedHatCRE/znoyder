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

import datetime
import logging
import sys

from znoyder.lib import logger
from znoyder.lib import zuul
from znoyder.lib.exceptions import PathError


LOG = logger.LOG


def find_jobs(directory, templates, pipelines):
    LOG.debug('Directory: %s' % directory)
    zuul_jobs = set()

    project = zuul.ZuulProject(project_path=directory,
                               templates=templates)

    zuul_jobs.update(project.get_list_of_jobs(pipelines))

    project_templates = project.get_list_of_used_templates()
    for template in reversed(project_templates):
        zuul_jobs.update(template.get_jobs(pipelines))

    return list(zuul_jobs)


def find_templates(directories, pipelines):
    LOG.debug('Directories: %s' % directories)

    zuul_templates = []

    for directory in directories.split(','):
        project = zuul.ZuulProject(project_path=directory)
        templates = project.get_list_of_defined_templates(pipelines)
        zuul_templates.extend(templates)

    return zuul_templates


def find_pipelines(pipelines):
    LOG.debug('Triggers: %s' % pipelines)

    pipelines_list = []

    for pipeline in pipelines.split(','):
        pipelines_list.append(zuul.ZuulPipeline.to_type(pipeline))

    return pipelines_list


def _cli_find_jobs(directory, templates, pipelines):
    LOG.debug('Project dir: %s' % directory)
    LOG.debug('Template dirs: %s' % templates)
    LOG.debug('Pipelines: %s' % pipelines)

    pipelines_list = []
    for pipeline in pipelines.split(','):
        pipelines_list.append(zuul.ZuulPipeline.to_type(pipeline))

    zuul_templates = []

    for template_dir in templates.split(','):
        project = zuul.ZuulProject(project_path=template_dir)
        templates = project.get_list_of_defined_templates(pipelines_list)
        zuul_templates.extend(templates)

    project = zuul.ZuulProject(project_path=directory,
                               templates=zuul_templates)

    zuul_jobs = project.get_list_of_jobs(pipelines_list)

    for job in zuul_jobs:
        print('%s: %s' % (job.pipeline, job))

    project_templates = project.get_list_of_used_templates()
    for template in project_templates:
        for job in template.get_jobs(pipelines_list):
            print('%s: %s in template %s' %
                  (job.pipeline, job, template))


def main(args) -> None:
    if args.verbose:
        LOG.setLevel(level=logging.DEBUG)
        LOG.debug('Shperer CLI running in debug mode')

    LOG.debug('%s' % args)

    start_time = datetime.datetime.now()

    try:
        _cli_find_jobs(args.directory,
                       args.templates,
                       args.pipeline)

    except PathError as ex:
        LOG.error(ex.message)
        sys.exit(1)

    finally:
        finish_time = datetime.datetime.now()
        LOG.debug('Finished shperer: %s' %
                  finish_time.strftime('%Y-%m-%d %H:%M:%S'))
        LOG.debug('Run time: %s [H]:[M]:[S].[ms]' %
                  str(finish_time - start_time))
