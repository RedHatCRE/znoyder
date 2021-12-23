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
import os.path

from zuuler import descarger
from zuuler import fertiger
from zuuler.lib import logger
from zuuler import shperer
from zuuler import znoyder


UPSTREAM_CONFIGS_DIR = 'jobs-upstream/'
GENERATED_CONFIGS_DIR = 'jobs-generated/'
CONFIG_PREFIX = 'cre-'
CONFIG_EXTENSION = '.yaml'

LOG = logger.LOG


def fetch_osp_projects(**kwargs) -> list:
    packages = znoyder.get_packages(upstream='opendev.org', **kwargs)
    repositories = [package.get('upstream') for package in packages]
    branch = 'master'

    if kwargs.get('tag'):
        release = znoyder.get_releases(**kwargs)[0].get('upstream_release')
        branch = f'stable/{release}'

    templates_repository = 'https://opendev.org/openstack/openstack-zuul-jobs'
    templates_branch = 'master'
    templates_urls = descarger.download_zuul_config(
        repository=templates_repository,
        branch=templates_branch,
        destination=UPSTREAM_CONFIGS_DIR,
        errors_fatal=False,
        skip_existing=True
    )
    templates_directory = list(templates_urls.keys())[0]

    directories = []
    for repository in repositories:
        project_urls = descarger.download_zuul_config(
            repository=repository,
            branch=branch,
            destination=UPSTREAM_CONFIGS_DIR,
            errors_fatal=False,
            skip_existing=True
        )
        for directory in project_urls.keys():
            directories.append(directory)

    return [templates_directory] + directories


def list_existing_osp_projects() -> list:
    templates_directory = 'openstack/openstack-zuul-jobs'

    directories = [os.path.join(namespace, project)
                   for namespace in os.listdir(UPSTREAM_CONFIGS_DIR)
                   for project in os.listdir(os.path.join(UPSTREAM_CONFIGS_DIR,
                                                          namespace))]
    if templates_directory in directories:
        directories.remove(templates_directory)

    return [templates_directory] + directories


def process_arguments() -> Namespace:
    parser = ArgumentParser()
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

    arguments = parser.parse_args()
    return arguments


def main() -> None:
    args = process_arguments()

    if args.download or not(os.path.exists(UPSTREAM_CONFIGS_DIR)):
        LOG.info('Downloading new Zuul configuration from upstream...')
        LOG.info(f'Zuul configuration files: {UPSTREAM_CONFIGS_DIR}')
        directories = fetch_osp_projects(**vars(args))
        templates_directory = directories.pop(0)
    else:
        LOG.info('Using local Zuul configuration files...')
        LOG.info(f'Path to Zuul configuration files: {UPSTREAM_CONFIGS_DIR}')
        directories = list_existing_osp_projects()
        templates_directory = directories.pop(0)

    if not args.generate:
        LOG.warning('Nothing else to do.')
        return

    LOG.info('Generating new downstream configuration files...')
    LOG.info(f'Output path: {GENERATED_CONFIGS_DIR}')
    triggers = shperer.find_triggers('check,gate')

    path = os.path.abspath(os.path.join(UPSTREAM_CONFIGS_DIR,
                                        templates_directory))
    templates = shperer.find_templates(path, triggers)

    for directory in directories:
        LOG.info(f'Processing: {directory}')
        path = os.path.abspath(os.path.join(UPSTREAM_CONFIGS_DIR,
                                            directory))
        jobs = shperer.find_jobs(path, templates, triggers)

        name = directory.replace('/', '-')
        config_dest = os.path.join(
            GENERATED_CONFIGS_DIR,
            CONFIG_PREFIX + name + CONFIG_EXTENSION
        )

        fertiger.generate_zuul_config(path=config_dest,
                                      name=name,
                                      jobs=jobs,
                                      collect_all=args.collect_all)


if __name__ == '__main__':
    main()
