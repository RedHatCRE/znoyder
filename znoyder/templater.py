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

import math
import os

from jinja2 import Environment
from jinja2 import PackageLoader
import yaml

from znoyder.lib import logger
from znoyder.lib.yaml import NestedDumper


LOG = logger.LOG

j2env = Environment(loader=PackageLoader('znoyder', 'templates'))


def generate_zuul_project_template(path: str, name: str, pipelines: dict):
    template = j2env.get_template('zuul-project-template.j2')

    config = template.render(name=name, pipelines=pipelines)
    config = yaml.safe_load(config)
    config = '---\n' + yaml.dump(
        config,
        Dumper=NestedDumper,
        default_flow_style=False,
        sort_keys=False,
        width=math.inf,
    )
    config = config.strip()

    with open(path, 'w') as file:
        file.write(config)
        file.write('\n')


def generate_zuul_projects_config(path: str, projects: list, prefix: str):
    template = j2env.get_template('zuul-projects-config.j2')

    config = template.render(projects=projects, prefix=prefix)
    config = config.strip()

    with open(path, 'w') as file:
        file.write(config)
        file.write('\n')


def generate_zuul_resources_config(path: str, projects: list, prefix: str):
    template = j2env.get_template('zuul-resources.j2')

    config = template.render(projects=projects, prefix=prefix)
    config = config.strip()

    with open(path, 'w') as file:
        file.write(config)
        file.write('\n')


def main(args) -> None:
    LOG.info('Available templates:')
    for template in j2env.list_templates():
        template = os.path.splitext(template)
        LOG.info(f'   - {template[0]}')
