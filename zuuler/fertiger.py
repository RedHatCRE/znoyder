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
import os.path
from pathlib import Path

from jinja2 import Template


JOBS_TO_COLLECT = [
    'openstack-tox-pep8',
    'openstack-tox-py36',
    'openstack-tox-py37',
    'openstack-tox-py38',
    'openstack-tox-py39',
]

JOBS_REMAPPING = {
    'openstack-tox-pep8': 'osp-tox-pep8',
    'openstack-tox-py36': 'osp-tox-py36',
    'openstack-tox-py37': 'osp-tox-py37',
    'openstack-tox-py38': 'osp-tox-py38',
    'openstack-tox-py39': 'osp-tox-py39',
}

JOB_TEMPLATE = Template('''
- project:
    name: {{ name }}
    {%- for type in jobs %}
    {{ type }}:
      jobs:
        {%- for job in jobs[type] %}
        - {{ job }}
        {%- endfor -%}
    {%- endfor -%}
''')


def generate_zuul_config(path: str, name: str, jobs: list,
                         collect_all: bool = False) -> bool:
    jobs_dict = defaultdict(list)

    for job in jobs:
        job_name = job.job_name

        if not collect_all and job_name not in JOBS_TO_COLLECT:
            continue

        if job_name in JOBS_REMAPPING:
            job_name = JOBS_REMAPPING[job_name]

        jobs_dict[job.job_trigger_type].append(job_name)

    if not jobs_dict:
        return False

    config = JOB_TEMPLATE.render(name=name, jobs=jobs_dict).strip()

    destination_directory = os.path.dirname(path)
    Path(destination_directory).mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as file:
        file.write(config)
        file.write('\n')

    return True


def main() -> None:
    print('Jobs being collected by default:')
    for job in JOBS_TO_COLLECT:
        if job in JOBS_REMAPPING:
            print(job, '->', JOBS_REMAPPING[job])
        else:
            print(job)


if __name__ == '__main__':
    main()
