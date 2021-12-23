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
from functools import partial
import json
from multiprocessing import cpu_count
from multiprocessing import Pool
import os.path
from pathlib import Path
from sys import exit

import requests

from zuuler.lib import logger


LOG = logger.LOG

GITHUB_API_URL = 'https://api.github.com/'
OPENDEV_API_URL = 'https://opendev.org/api/v1/'

REPO_ENDPOINT = 'repos/{project}/'
CONTENT_ENDPOINT = 'contents/{path}?ref={gitref}'


def get_raw_url_files_in_repository(repository: str,
                                    data_required: dict,
                                    branch: str = 'master',
                                    errors_fatal: bool = True) -> dict:
    if 'opendev.org' in repository:
        ENDPOINT = (OPENDEV_API_URL + REPO_ENDPOINT + CONTENT_ENDPOINT)
    elif 'github.com' in repository:
        ENDPOINT = (GITHUB_API_URL + REPO_ENDPOINT + CONTENT_ENDPOINT)
    else:
        LOG.error('Unrecognized or unsupported repository host.')
        LOG.error('The tool supports github.com and opendev.org repositories.')
        if errors_fatal:
            exit(1)
        else:
            return {}

    project_name = '/'.join(repository.split('/')[-2:])
    response = requests.get(url=ENDPOINT.format(project=project_name,
                                                path='.',
                                                gitref=branch))

    LOG.info(f'Requested: {response.url}')
    if response.status_code != 200:
        LOG.error('Error getting URLs from directory in remote repository.')
        details = json.loads(response.text).get('errors',
                                                json.loads(response.text))
        LOG.error(f'Details: {repr(details)}')
        if errors_fatal:
            exit(1)
        else:
            return {}

    url_files = {}

    for directory_file_information in json.loads(response.text):
        file_name = directory_file_information['name']

        if file_name in data_required['files']:
            url_files.setdefault(project_name, []).append(
                directory_file_information['download_url']
            )

        if file_name in data_required['directories']:
            response = requests.get(url=ENDPOINT.format(project=project_name,
                                                        path=file_name,
                                                        gitref=branch))

            for directory_file_information in json.loads(response.text):
                if directory_file_information['type'] != 'file':
                    continue

                url_files.setdefault(f'{project_name}/{file_name}', []).append(
                    directory_file_information['download_url']
                )

    return url_files


def download_file(url: str, destination_directory: str,
                  ignore_existing: bool = False) -> None:
    Path(destination_directory).mkdir(parents=True, exist_ok=True)
    file_name = url.split('/')[-1]
    file_path = f'{destination_directory}/{file_name}'

    if os.path.exists(file_path):
        LOG.warning(f'File already exists: {file_name}')

    if ignore_existing:
        LOG.info(f'Skipping the download of file: {file_name}')
        return

    try:
        LOG.info(f'Downloading new file: {file_name}')
        data = requests.get(url)
        with open(file_path, 'wb') as file:
            file.write(data.content)

    except Exception as e:
        LOG.error(f'Error downloading file: {file_name}.\nDetails: {repr(e)}')
        exit(1)


def download_files_parallel(urls: list, destination_directory: str,
                            ignore_existing: bool = False) -> None:
    pool = Pool(cpu_count())

    download_function = partial(
        download_file,
        destination_directory=destination_directory,
        ignore_existing=ignore_existing
    )

    pool.map(download_function, urls)
    pool.close()
    pool.join()


def download_zuul_config(**kwargs):
    data_wanted = {
        'directories': ['zuul.d', '.zuul.d'],
        'files': ['zuul.yaml', '.zuul.yaml']
    }

    repository = kwargs.get('repository')
    branch = kwargs.get('branch')
    destination = kwargs.get('destination')
    errors_fatal = kwargs.get('errors_fatal', True)
    ignore_existing = kwargs.get('ignore_existing', False)

    project_urls = get_raw_url_files_in_repository(
        repository,
        data_wanted,
        branch,
        errors_fatal
    )

    for project_directory in project_urls:
        download_files_parallel(project_urls[project_directory],
                                f'{destination}/{project_directory}',
                                ignore_existing=ignore_existing)

    return project_urls


def process_arguments() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        '-r', '--repo', '--repository',
        dest='repository',
        help='repository to browse for files',
        metavar='REPOSITORY',
        required=True
    )
    parser.add_argument(
        '-b', '--branch',
        dest='branch',
        help='branch in repository to browse',
        metavar='BRANCH',
        required=True
    )
    parser.add_argument(
        '-d', '--destination',
        dest='destination',
        help='target directory for files to save',
        metavar='DESTINATION',
        required=True
    )
    parser.add_argument(
        '-n', '--non-fatal', '--errors-non-fatal',
        dest='errors_fatal',
        default=True,
        action='store_false',
        help='do not fail on non-existing remote'
    )
    parser.add_argument(
        '-i', '--ignore', '--ignore-existing',
        dest='ignore_existing',
        default=False,
        action='store_true',
        help='do not overwrite existing files'
    )

    arguments = parser.parse_args()
    return arguments


def main() -> None:
    arguments = process_arguments()

    download_zuul_config(**vars(arguments))


if __name__ == '__main__':
    main()
