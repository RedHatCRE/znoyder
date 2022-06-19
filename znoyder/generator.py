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
from shutil import rmtree

from znoyder import browser
from znoyder.config import branches_map
from znoyder.config import GENERATED_CONFIGS_DIR
from znoyder.config import GENERATED_CONFIG_PREFIX
from znoyder.config import GENERATED_CONFIG_EXTENSION
from znoyder.config import UPSTREAM_CONFIGS_DIR
from znoyder import downloader
from znoyder import finder
from znoyder.lib import logger
from znoyder import mapper
from znoyder import templater


LOG = logger.LOG


def cleanup_generated_jobs_dir() -> None:
    if os.path.exists(GENERATED_CONFIGS_DIR):
        rmtree(GENERATED_CONFIGS_DIR)
        LOG.info(f'Removed the directory: {GENERATED_CONFIGS_DIR}')

    destination_directory = os.path.join(GENERATED_CONFIGS_DIR,
                                         'osp-internal-jobs-config', 'zuul.d')
    Path(destination_directory).mkdir(parents=True, exist_ok=True)

    destination_directory = os.path.join(GENERATED_CONFIGS_DIR,
                                         'osp-internal-jobs', 'zuul.d')
    Path(destination_directory).mkdir(parents=True, exist_ok=True)

    destination_directory = os.path.join(GENERATED_CONFIGS_DIR,
                                         'sf-config', 'resources')
    Path(destination_directory).mkdir(parents=True, exist_ok=True)


def fetch_templates_directory():
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

    return templates_directory


def fetch_osp_projects(branch: str, filters: dict) -> list:
    projects = {package.get('osp-project'): package.get('upstream')
                for package in browser.get_packages(**filters)}

    for osp_name, repository in projects.items():
        project_urls = downloader.download_zuul_config(
            repository=repository,
            branch=branch,
            destination=UPSTREAM_CONFIGS_DIR,
            errors_fatal=False,
            skip_existing=True
        )

        for directory in project_urls.keys():
            projects[osp_name] = directory

    return projects


def discover_jobs(project_name, osp_tag, directory,
                  templates, pipelines) -> list:
    jobs = []

    if directory:
        path = os.path.abspath(os.path.join(UPSTREAM_CONFIGS_DIR,
                                            directory))
        if os.path.exists(path):
            LOG.info(f'Including from: {directory}')
            upstream_jobs = finder.find_jobs(path, templates, pipelines)
            jobs = mapper.include_jobs(upstream_jobs, osp_tag)

    jobs = mapper.exclude_jobs(jobs, project_name, osp_tag)
    jobs = mapper.add_jobs(jobs, project_name, osp_tag)
    jobs = mapper.override_jobs(jobs, project_name, osp_tag)
    jobs = mapper.copy_jobs(jobs, project_name, osp_tag)

    LOG.info(f'Jobs number: {len(jobs)}')
    for job in jobs:
        LOG.debug(f'{job.pipeline}/{job.name}:{job.parameters}')

    return jobs


def generate_projects_pipleines_dict(args):
    # The scheme is: projects{} -> pipelines{} -> jobs[]
    projects_pipelines_dict = defaultdict(lambda: defaultdict(list))

    if args.tag:
        tags = args.tag.split(',')
    else:
        tags = list(branches_map.keys())

    for osp_tag in tags:
        upstream_branch = branches_map.get(osp_tag, {}).get('upstream')
        downstream_branch = branches_map.get(osp_tag, {}).get('downstream')

        ospinfo_filters = {'tag': osp_tag}
        if args.name:
            ospinfo_filters['name'] = args.name
        if args.component:
            ospinfo_filters['component'] = args.component

        LOG.info('Downloading Zuul configuration from upstream...')
        LOG.info(f'Zuul configuration files: {UPSTREAM_CONFIGS_DIR}')
        templates_directory = fetch_templates_directory()
        projects = fetch_osp_projects(
            branch=upstream_branch,
            filters=ospinfo_filters,
        )

        path = os.path.abspath(os.path.join(UPSTREAM_CONFIGS_DIR,
                                            templates_directory))

        pipelines = finder.find_pipelines('check,gate')
        templates = finder.find_templates(path, pipelines)

        LOG.info('Generating new downstream configuration files...')
        LOG.info(f'Output path: {GENERATED_CONFIGS_DIR}')

        for project_name, directory in projects.items():
            LOG.info(f'Processing: {project_name}')
            jobs = discover_jobs(project_name, osp_tag, directory,
                                 templates, pipelines)

            if not jobs:
                projects_pipelines_dict[project_name] = {}

            for job in jobs:
                projects_pipelines_dict[project_name][job.pipeline].append(
                    {
                        'name': job.name,
                        'branch': downstream_branch,
                        'parameters': job.parameters,
                        'voting': job.parameters.pop('voting', 'false'),
                    }
                )

    return projects_pipelines_dict


def generate_projects_templates(projects_pipelines_dict: dict) -> None:
    for project_name in projects_pipelines_dict:
        pipelines = projects_pipelines_dict[project_name]
        config_dest = os.path.join(
            GENERATED_CONFIGS_DIR,
            'osp-internal-jobs', 'zuul.d',
            GENERATED_CONFIG_PREFIX + project_name + GENERATED_CONFIG_EXTENSION
        )

        templater.generate_zuul_project_template(
            path=config_dest,
            name=GENERATED_CONFIG_PREFIX + project_name,
            pipelines=pipelines
        )


def generate_projects_config(projects_pipelines_dict: dict) -> None:
    projects = list(projects_pipelines_dict.keys())
    config_dest = os.path.join(
        GENERATED_CONFIGS_DIR,
        'osp-internal-jobs-config', 'zuul.d',
        GENERATED_CONFIG_PREFIX + 'projects' + GENERATED_CONFIG_EXTENSION
    )

    templater.generate_zuul_projects_config(
        path=config_dest,
        projects=projects,
        prefix=GENERATED_CONFIG_PREFIX
    )


def generate_resources_config(projects_pipelines_dict: dict) -> None:
    projects = list(projects_pipelines_dict.keys())
    config_dest = os.path.join(
        GENERATED_CONFIGS_DIR,
        'sf-config', 'resources',
        'osp-internal' + GENERATED_CONFIG_EXTENSION
    )

    templater.generate_zuul_resources_config(
        path=config_dest,
        projects=projects,
        prefix=GENERATED_CONFIG_PREFIX
    )


def main(args) -> None:
    cleanup_generated_jobs_dir()
    projects_pipelines_dict = generate_projects_pipleines_dict(args)
    generate_projects_templates(projects_pipelines_dict)
    generate_projects_config(projects_pipelines_dict)
    generate_resources_config(projects_pipelines_dict)
