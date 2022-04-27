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

from collections import defaultdict
import os
import sys

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2.exceptions import TemplateNotFound
import yaml

from znoyder.lib import logger


LOG = logger.LOG

j2env = Environment(loader=PackageLoader('znoyder', 'templates'))


class NestedDumper(yaml.Dumper):
    # by https://stackoverflow.com/a/39681672
    def increase_indent(self, flow=False, indentless=False):
        return super(NestedDumper, self).increase_indent(flow, False)


def _is_job_already_defined(jobs_dict: list, job_name: str, trigger_type: str):
    jobs = jobs_dict.get(trigger_type)

    if isinstance(jobs, list):
        for job in jobs:
            if job_name in job:
                return True
    return False


def generate_zuul_config(path: str, name: str,
                         project_template: str,
                         jobs: list,
                         branch_regex: str,
                         template_name: str = None,
                         collect_all: bool = False,
                         write_mode: str = 'w',
                         voting: bool = False) -> bool:

    jobs_dict = defaultdict(list)

    try:
        JOB_TEMPLATE = j2env.get_template(template_name+".j2")
    except TemplateNotFound:
        LOG.error(f'Template "{template_name}" does not exist')
        LOG.info('Please use one of the following templates or add your own')
        LOG.info('Available templates:')
        for template in j2env.list_templates():
            template = os.path.splitext(template)
            LOG.info(f'   - {template[0]}')
        sys.exit()

    for job in jobs:
        job_name = job.job_name

        LOG.info(f'Collecting job: {job_name}')
        if not _is_job_already_defined(jobs_dict, job_name,
                                       job.job_trigger_type):

            templated_job = {
                job_name: {
                    'voting': job.job_data.pop('voting', str(voting).lower()),
                    'branch_regex': branch_regex,
                    'job_data': job.job_data,
                }
            }

            jobs_dict[job.job_trigger_type].append(templated_job)

    if not jobs_dict:
        LOG.error('No jobs collected, skipping config generation.')
        return False

    config = JOB_TEMPLATE.render(name=project_template, jobs=jobs_dict).strip()

    config = yaml.safe_load(config)
    config = yaml.dump(
        config,
        Dumper=NestedDumper,
        default_flow_style=False,
        sort_keys=False,
    )
    config = '---\n' + config
    config = config.strip()

    if write_mode == 'a' and config[0:4] == '---\n':
        config = config[4:]

    with open(path, write_mode) as file:
        file.write(config)
        file.write('\n')

    return True


def main(args) -> None:
    LOG.info('Available templates:')
    for template in j2env.list_templates():
        template = os.path.splitext(template)
        LOG.info(f'   - {template[0]}')
