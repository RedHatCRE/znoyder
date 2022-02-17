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

from copy import deepcopy
import os.path
from pathlib import Path
from shutil import rmtree

from znoyder import downloader
from znoyder.exclude_map import excluded_jobs
from znoyder.exclude_map import excluded_jobs_by_tag
from znoyder.exclude_map import excluded_jobs_by_project_and_tag
from znoyder.include_map import additional_jobs
from znoyder.include_map import additional_jobs_by_tag
from znoyder.include_map import additional_jobs_by_project_and_tag
from znoyder import templater
from znoyder.lib import logger
from znoyder.package import Package
from znoyder.lib.zuul import ZuulJob
from znoyder import finder
from znoyder import browser


UPSTREAM_CONFIGS_DIR = 'jobs-upstream/'
GENERATED_CONFIGS_DIR = 'jobs-generated/'
CONFIG_PREFIX = 'cre-'
CONFIG_EXTENSION = '.yaml'

# We set it to newest
DEFAULT_BRANCH_REGEX = '^rhos-17.*$'

LOG = logger.LOG


def fetch_osp_projects(**kwargs) -> list:
    packages = Package.get_osp_packages(upstream='opendev.org', **kwargs)
    repositories = [package.upstream for package in packages
                    if package.upstream]
    branch = 'master'

    if kwargs.get('tag'):
        release = browser.get_releases(**kwargs)[0].get('upstream_release')
        branch = f'stable/{release}'

    templates_repository = 'https://opendev.org/openstack/openstack-zuul-jobs'
    templates_branch = 'master'
    templates_urls = downloader.download_zuul_config(
        repository=templates_repository,
        branch=templates_branch,
        destination=UPSTREAM_CONFIGS_DIR,
        errors_fatal=False,
        skip_existing=True
    )
    templates_directory = list(templates_urls.keys())[0]

    directories = []
    for repository in repositories:
        project_urls = downloader.download_zuul_config(
            repository=repository,
            branch=branch,
            destination=UPSTREAM_CONFIGS_DIR,
            errors_fatal=False,
            skip_existing=True
        )
        for directory in project_urls.keys():
            directories.append(directory)

    return [templates_directory] + directories


def exclude_jobs(jobs, project, tag) -> list:
    """Returns list of jobs filtered by exclude map variables.

    Args:
        jobs: List of jobs
        project: A project name string
        tag: A tag string

    Returns:
        List of of jobs after being filtered with the exclude maps
    """
    included_jobs = []

    for job in jobs:
        if job.job_name in excluded_jobs:
            continue

        if tag in excluded_jobs_by_tag \
           and job.job_name in excluded_jobs_by_tag[tag]:
            continue

        if project in excluded_jobs_by_project_and_tag \
           and tag in excluded_jobs_by_project_and_tag[project] \
           and job.job_name in excluded_jobs_by_project_and_tag[project][tag]:
            continue
        included_jobs.append(job)

    return included_jobs


def include_jobs(jobs, project, tag) -> list:
    included_jobs = deepcopy(jobs)

    def job_from_entry(entry: dict) -> ZuulJob:
        job_name, job_options = deepcopy(entry)
        job_trigger_type = job_options.pop('type', 'check')

        if isinstance(job_trigger_type, str):
            return [ZuulJob(job_name, job_trigger_type, job_options)]
        else:
            return [ZuulJob(job_name, trigger_type, job_options)
                    for trigger_type in job_trigger_type]

    for entry in additional_jobs.items():
        included_jobs.extend(job_from_entry(entry))

    if tag in additional_jobs_by_tag:
        for entry in additional_jobs_by_tag[tag].items():
            included_jobs.extend(job_from_entry(entry))

    if project in additional_jobs_by_project_and_tag \
       and tag in additional_jobs_by_project_and_tag[project]:
        for entry in additional_jobs_by_project_and_tag[project][tag].items():
            included_jobs.extend(job_from_entry(entry))

    return included_jobs


def list_existing_osp_projects() -> list:
    templates_directory = 'openstack/openstack-zuul-jobs'

    directories = [os.path.join(namespace, project)
                   for namespace in os.listdir(UPSTREAM_CONFIGS_DIR)
                   for project in os.listdir(os.path.join(UPSTREAM_CONFIGS_DIR,
                                                          namespace))]
    if templates_directory in directories:
        directories.remove(templates_directory)

    return [templates_directory] + directories


def cleanup_generated_jobs_dir() -> None:
    if os.path.exists(GENERATED_CONFIGS_DIR):
        rmtree(GENERATED_CONFIGS_DIR)
        LOG.info('Removed the directory: {GENERATED_CONFIGS_DIR}')
    destination_directory = os.path.dirname(GENERATED_CONFIGS_DIR)
    Path(destination_directory).mkdir(parents=True, exist_ok=True)


def extend_parser(parser) -> None:
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
        '--aggregate',
        dest='aggregate',
        help='File path where all templates will be aggregated'
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
    parser.add_argument(
        '-m', '--template-name',
        dest='template',
        default='zuul-project',
        help='Use defined template name, e.g. empty-zuul-project'
    )


def main(args) -> None:
    cleanup_generated_jobs_dir()

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

    LOG.info('Generating new downstream configuration files...')
    LOG.info(f'Output path: {GENERATED_CONFIGS_DIR}')
    triggers = finder.find_triggers('check,gate')

    path = os.path.abspath(os.path.join(UPSTREAM_CONFIGS_DIR,
                                        templates_directory))
    templates = finder.find_templates(path, triggers)

    us_to_ds_projects_map = browser.get_projects_mapping()

    if args.aggregate:
        config_dest = os.path.join(GENERATED_CONFIGS_DIR, args.aggregate)
        write_mode = 'a'
        with open(config_dest, write_mode) as f:
            f.write('---\n')

    additional_projects = [
        name
        for name in additional_jobs_by_project_and_tag.keys()
        if name not in directories
    ]
    directories.extend(additional_projects)

    for directory in directories:
        LOG.info(f'Processing: {directory}')
        path = os.path.abspath(os.path.join(UPSTREAM_CONFIGS_DIR,
                                            directory))
        if os.path.exists(path):
            jobs = finder.find_jobs(path, templates, triggers)
        else:
            jobs = []

        # Case where zuul configs are inside zuul.d
        directory = directory.replace('/zuul.d', '').replace('/.zuul.d', '')
        name = directory.replace('/', '-')

        if name in us_to_ds_projects_map.keys():
            ds_name = us_to_ds_projects_map[name]
        else:
            ds_name = name

        jobs = exclude_jobs(jobs, ds_name, args.tag)
        jobs = include_jobs(jobs, ds_name, args.tag)

        if not args.aggregate:
            config_dest = os.path.join(
                GENERATED_CONFIGS_DIR,
                CONFIG_PREFIX + ds_name + CONFIG_EXTENSION
            )
            write_mode = 'w'

        branch_regex = DEFAULT_BRANCH_REGEX

        if args.tag and args.tag.startswith('osp-'):
            branch_regex = '%s.*$' % \
              args.tag.replace('osp', '^rhos').split('.')[0]

        templater.generate_zuul_config(
            path=config_dest,
            template_name=args.template,
            project_template=CONFIG_PREFIX + ds_name,
            name=ds_name,
            jobs=jobs,
            collect_all=args.collect_all,
            write_mode=write_mode,
            branch_regex=branch_regex)


if __name__ == '__main__':
    main()
