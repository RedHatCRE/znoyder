#!/usr/bin/env python3
#
# Copyright 2022 Red Hat, Inc.
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
import re
import sys

from znoyder.config import add_map
from znoyder.config import copy_map
from znoyder.config import exclude_map
from znoyder.config import include_map
from znoyder.config import override_map
from znoyder.lib import logger
from znoyder.lib.zuul import ZuulJob


LOG = logger.LOG


def match(string: str, specifier: str) -> bool:
    '''Function checks if a given string is matched by a given specifier.

    The match is performed in the awk-inspired fashion:
    – if the specifier starts and ends with the forward slash (/), e.g. /foo/,
      then the content between slashes is treated as regular expression,
    – otherwise it is a value that should fully match the input string.

    Parameters
    ----------
    string : str
        The string that should be tested against specifier.
    specifier : str
        The expected value or regular expression to be matched against.

    Returns
    -------
    matched : bool
        True if given string matches the specifier, False otherwise.

    Examples
    --------
    >>> match('foobar', 'foobar')
    True
    >>> match('foobar', 'foo')
    False
    >>> match('foobar', '/foo/')
    True
    '''

    if specifier.startswith('/') and specifier.endswith('/'):
        regex = re.compile(specifier[1:-2])
        return bool(regex.search(string))
    else:
        regex = re.compile(specifier)
        return bool(regex.fullmatch(string))


def new_jobs_from_map_entry(entry: dict) -> ZuulJob:
    job_name, job_options = entry
    pipeline = job_options.pop('pipeline', 'check')

    if isinstance(pipeline, str):
        return [ZuulJob(job_name, pipeline, job_options)]
    else:
        return [ZuulJob(job_name, pipeline, job_options)
                for pipeline in pipeline]


def update_jobs_from_map_entry(jobs: list, entry: dict) -> list:
    job_name, job_options = entry
    pipeline = job_options.pop('pipeline', '/.*/')  # any pipeline by default

    for index, job in enumerate(jobs):
        if (match(job.name, job_name)
                and match(job.pipeline, pipeline)):
            jobs[index].parameters.update(job_options)

            for key, value in jobs[index].parameters.copy().items():
                if value is None:
                    del jobs[index].parameters[key]

    return jobs


def copy_jobs_from_map_entry(jobs: list, entry: dict) -> list:
    job_name, job_options = tuple(deepcopy(entry).items())[0]
    pipeline = job_options.pop('from', '/.*/')  # any pipeline by default
    new_pipeline = job_options.pop('to', None)
    new_name = job_options.pop('as', job_name)

    if job_name == new_name and not new_pipeline:
        LOG.error(f'Bad entry definition: {entry}')
        LOG.error('Target pipeline or unique new name shall be specified.')
        sys.exit(1)

    new_jobs = []

    for index, job in enumerate(jobs):
        if match(job.name, job_name) and match(job.pipeline, pipeline):
            new_job = deepcopy(job)
            new_job.parameters.update(job_options)

            for key, value in new_job.parameters.copy().items():
                if value is None:
                    del new_job.parameters[key]

            if new_name:
                new_job.name = new_name
            if new_pipeline:
                new_job.pipeline = new_pipeline

            new_jobs.append(new_job)

    jobs.extend(new_jobs)

    return jobs


def include_jobs(jobs, tag) -> list:
    upstream_jobs = deepcopy(jobs)
    collected_jobs = []
    jobs_to_collect = include_map.get(tag, {})

    for job in upstream_jobs:
        if job.name not in jobs_to_collect:
            LOG.warning(f'Ignoring job: {job.name}')
            continue

        if jobs_to_collect.get(job.name) is not None:
            new_name = jobs_to_collect[job.name]
            LOG.info(f'Renaming job: {job.name} -> {new_name}'
                     f' ({job.pipeline})')
            job.name = new_name

        LOG.info(f'Included job: {job.name} ({job.pipeline})')
        collected_jobs.append(job)

    return collected_jobs


def exclude_jobs(jobs, project, tag) -> list:
    for project_specifier in exclude_map:
        if not match(project, project_specifier):
            continue

        for tag_specifier in exclude_map[project_specifier]:
            if not match(tag, tag_specifier):
                continue

            exclude_map_jobs = exclude_map[project_specifier][tag_specifier]
            for job_specifier in exclude_map_jobs.keys():
                jobs = [job for job in jobs
                        if not match(job.name, job_specifier)]

    return jobs


def add_jobs(jobs, project, tag) -> list:
    for project_specifier in add_map:
        if not match(project, project_specifier):
            continue

        for tag_specifier in add_map[project_specifier]:
            if not match(tag, tag_specifier):
                continue

            add_map_jobs = add_map[project_specifier][tag_specifier]
            for job_entry in add_map_jobs.items():
                jobs.extend(new_jobs_from_map_entry(job_entry))

    return jobs


def override_jobs(jobs, project, tag) -> list:
    for project_specifier in override_map:
        if not match(project, project_specifier):
            continue

        for tag_specifier in override_map[project_specifier]:
            if not match(tag, tag_specifier):
                continue

            override_map_jobs = override_map[project_specifier][tag_specifier]
            for job_entry in override_map_jobs.items():
                jobs = update_jobs_from_map_entry(jobs, job_entry)

    return jobs


def copy_jobs(jobs, project, tag) -> list:
    for project_specifier in copy_map:
        if not match(project, project_specifier):
            continue

        for tag_specifier in copy_map[project_specifier]:
            if not match(tag, tag_specifier):
                continue

            for map_entry in copy_map[project_specifier][tag_specifier]:
                jobs = copy_jobs_from_map_entry(jobs, map_entry)

    return jobs
