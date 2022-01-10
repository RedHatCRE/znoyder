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
from collections import defaultdict
import os.path
from pathlib import Path

from jinja2 import Environment
from jinja2 import PackageLoader

from znoyder.lib import logger


LOG = logger.LOG

JOBS_TO_COLLECT_WITH_MAPPING = {
    'openstack-tox-pep8': 'osp-tox-pep8',
    'openstack-tox-py36': 'osp-tox-py36',
    'openstack-tox-py37': 'osp-tox-py37',
    'openstack-tox-py38': 'osp-tox-py38',
    'openstack-tox-py39': 'osp-tox-py39',
}

j2env = Environment(loader=PackageLoader('znoyder', 'templates'))


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
                         voting: bool = False) -> bool:

    jobs_dict = defaultdict(list)

    for job in jobs:
        job_name = job.job_name

        if not collect_all and job_name not in JOBS_TO_COLLECT_WITH_MAPPING:
            LOG.warning(f'Ignoring job: {job_name}')
            continue

        if JOBS_TO_COLLECT_WITH_MAPPING.get(job_name) is not None:
            new_name = JOBS_TO_COLLECT_WITH_MAPPING[job_name]
            LOG.info(f'Renaming job: {job_name} -> {new_name}')
            job_name = new_name

        LOG.info(f'Collecting job: {job_name}')
        if not _is_job_already_defined(jobs_dict, job_name,
                                       job.job_trigger_type):

            templated_job = {
                job_name: {
                    'voting': voting,
                    'branch_regex': branch_regex
                }
            }

            jobs_dict[job.job_trigger_type].append(templated_job)

    if not jobs_dict:
        LOG.error('No jobs collected, skipping config generation.')
        return False

    JOB_TEMPLATE = j2env.get_template(template_name+".j2")

    config = JOB_TEMPLATE.render(name=project_template, jobs=jobs_dict).strip()

    destination_directory = os.path.dirname(path)
    Path(destination_directory).mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as file:
        file.write(config)
        file.write('\n')

    return True


def process_arguments(argv=None) -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        '-j', '--json',
        dest='json',
        default=False,
        action='store_true',
        help='produce output in JSON format'
    )

    arguments = parser.parse_args(argv)
    return arguments


def main(argv=None) -> None:
    args = process_arguments(argv)

    if args.json:
        print(JOBS_TO_COLLECT_WITH_MAPPING)
    else:
        print('Jobs being collected by default:')
        for job in JOBS_TO_COLLECT_WITH_MAPPING:
            if JOBS_TO_COLLECT_WITH_MAPPING[job] is not None:
                print(job, '->', JOBS_TO_COLLECT_WITH_MAPPING[job])
            else:
                print(job)


if __name__ == '__main__':
    main()
