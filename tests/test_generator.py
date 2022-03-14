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
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

import znoyder.browser
import znoyder.downloader
from znoyder.generator import GENERATED_CONFIGS_DIR
from znoyder.generator import UPSTREAM_CONFIGS_DIR
from znoyder.generator import additional_jobs
from znoyder.generator import additional_jobs_by_project_and_tag
from znoyder.generator import additional_jobs_by_tag
from znoyder.generator import cleanup_generated_jobs_dir
from znoyder.generator import exclude_jobs
from znoyder.generator import excluded_jobs
from znoyder.generator import excluded_jobs_by_tag
from znoyder.generator import excluded_jobs_by_project_and_tag
from znoyder.generator import fetch_osp_projects
from znoyder.generator import include_jobs
from znoyder.generator import list_existing_osp_projects
from znoyder.lib.zuul import ZuulJob


class TestFetchOSPProjects(TestCase):
    TEMPLATES_REPOSITORY = 'https://opendev.org/openstack/openstack-zuul-jobs'
    PACKAGE_REPOSITORY = 'http://localhost:8080/my/package'

    TEMPLATES_DIR = 'openstack/openstack-zuul-jobs/zuul.d'
    PACKAGE_DIR = 'my/package'

    def download_zuul_config(self, **kwargs):
        if kwargs.get('repository') == self.TEMPLATES_REPOSITORY:
            return {
                self.TEMPLATES_DIR: []
            }
        elif kwargs.get('repository') == self.PACKAGE_REPOSITORY:
            return {
                self.PACKAGE_DIR: []
            }
        else:
            raise RuntimeError('Repository not supported by this test')

    def test_happy_path(self):
        kwargs = {'arg1': 'val1'}

        package = {
            'upstream': 'http://localhost:8080/my/package'
        }

        packages = [package]

        pkgs_call = znoyder.browser.get_packages = Mock()
        templs_call = znoyder.downloader.download_zuul_config = Mock()

        pkgs_call.return_value = packages
        templs_call.side_effect = self.download_zuul_config

        self.assertEqual(
            [self.TEMPLATES_DIR, self.PACKAGE_DIR],
            fetch_osp_projects(**kwargs)
        )

        pkgs_call.assert_called_with(
            **kwargs,
            upstream='opendev.org'
        )

        templs_call.assert_any_call(
            repository=self.TEMPLATES_REPOSITORY,
            branch='master',
            destination=UPSTREAM_CONFIGS_DIR,
            errors_fatal=False,
            skip_existing=True
        )

        templs_call.assert_any_call(
            repository=self.PACKAGE_REPOSITORY,
            branch='master',
            destination=UPSTREAM_CONFIGS_DIR,
            errors_fatal=False,
            skip_existing=True
        )

    def test_filter_by_tag(self):
        kwargs = {'tag': []}

        package = {
            'upstream': 'http://localhost:8080/my/package'
        }

        release = {
            'upstream_release': 'release_branch'
        }

        packages = [package]
        releases = [release]

        pkgs_call = znoyder.browser.get_packages = Mock()
        rels_call = znoyder.browser.get_releases = Mock()
        templs_call = znoyder.downloader.download_zuul_config = Mock()

        pkgs_call.return_value = packages
        rels_call.return_value = releases
        templs_call.side_effect = self.download_zuul_config

        fetch_osp_projects(**kwargs)

        rels_call.assert_called_with(**kwargs)

        templs_call.assert_any_call(
            repository=self.PACKAGE_REPOSITORY,
            branch='stable/%s' % release['upstream_release'],
            destination=UPSTREAM_CONFIGS_DIR,
            errors_fatal=False,
            skip_existing=True
        )


class TestExcludeJobs(TestCase):
    def setUp(self) -> None:
        excluded_jobs.clear()
        excluded_jobs_by_tag.clear()
        excluded_jobs_by_project_and_tag.clear()

    def test_happy_path(self):
        self.assertEqual([], exclude_jobs([], '', ''))

    def test_exclude_by_name(self):
        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        excluded_jobs[job2.job_name] = ''

        self.assertEqual([job1], exclude_jobs([job1, job2], '', ''))

    def test_exclude_by_tag(self):
        tag = 'tag_1'

        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        excluded_jobs_by_tag[tag] = {job2.job_name: ''}

        self.assertEqual([job1], exclude_jobs([job1, job2], '', tag))

    def test_exclude_by_tag_and_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        excluded_jobs_by_project_and_tag[project] = {
            tag: {
                job2.job_name: ''
            }
        }

        self.assertEqual([job1], exclude_jobs([job1, job2], project, tag))


class TestIncludeJobs(TestCase):
    def setUp(self) -> None:
        additional_jobs.clear()
        additional_jobs_by_tag.clear()
        additional_jobs_by_project_and_tag.clear()

    def test_happy_path(self):
        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        jobs = [job1, job2]

        result = include_jobs(jobs, '', '')

        for i, _ in enumerate(result):
            self.assertEqual(jobs[i].job_name, result[i].job_name)

    def test_include_by_name(self):
        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        jobs = [job1]

        additional_jobs[job2.job_name] = {}

        result = include_jobs(jobs, '', '')

        for i, _ in enumerate(result):
            self.assertEqual([job1, job2][i].job_name, result[i].job_name)

    def test_include_by_tag(self):
        tag = 'tag_1'

        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        jobs = [job1]

        additional_jobs_by_tag[tag] = {
            job2.job_name: {}
        }

        result = include_jobs(jobs, '', tag)

        for i, _ in enumerate(result):
            self.assertEqual([job1, job2][i].job_name, result[i].job_name)

    def test_include_by_tag_and_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        jobs = [job1]

        additional_jobs_by_project_and_tag[project] = {
            tag: {
                job2.job_name: {}
            }
        }

        result = include_jobs(jobs, project, tag)

        for i, _ in enumerate(result):
            self.assertEqual([job1, job2][i].job_name, result[i].job_name)

    def test_job_generation_without_type(self):
        job_name = 'job_1'
        job_options = {'opt_1': 'val_1'}

        additional_jobs[job_name] = job_options

        result = include_jobs([], '', '')[0]

        self.assertIsInstance(result, ZuulJob)

        self.assertEqual(job_name, result.job_name)
        self.assertEqual('check', result.job_trigger_type)
        self.assertEqual(job_options, result.job_data)

    def test_job_generation_with_type(self):
        job_name = 'job_1'
        job_type = 'type'
        job_options = {'opt_1': 'val_1'}

        additional_jobs[job_name] = {'type': job_type} | job_options

        result = include_jobs([], '', '')[0]

        self.assertIsInstance(result, ZuulJob)

        self.assertEqual(job_name, result.job_name)
        self.assertEqual(job_type, result.job_trigger_type)
        self.assertEqual(job_options, result.job_data)


class TestListExistingOSPProjects(TestCase):
    def test_happy_path(self):
        namespace = 'namespace_1'
        project = 'project_1'

        def listdir(path):
            if path == UPSTREAM_CONFIGS_DIR:
                return [namespace]
            else:
                return [project]

        listdir_call = znoyder.generator.os.listdir = Mock()
        listdir_call.side_effect = listdir

        self.assertEqual(
            [
                'openstack/openstack-zuul-jobs',
                '%s/%s' % (namespace, project)
            ],
            list_existing_osp_projects()
        )

    def test_template_directory_is_not_repeated(self):
        namespace = 'openstack'
        project = 'openstack-zuul-jobs'

        def listdir(path):
            if path == UPSTREAM_CONFIGS_DIR:
                return [namespace]
            else:
                return [project]

        listdir_call = znoyder.generator.os.listdir = Mock()
        listdir_call.side_effect = listdir

        self.assertEqual(
            ['openstack/openstack-zuul-jobs'],
            list_existing_osp_projects()
        )


class TestCleanupGeneratedJobDir(TestCase):
    @patch('znoyder.generator.Path', autospec=True)
    def test_happy_path(self, path_call):
        dest_dir = 'path/to/dest/dir'

        path_mock = Mock()
        mkdir_mock = Mock()

        exists_call = znoyder.generator.os.path.exists = Mock()
        dirname_call = znoyder.generator.os.path.dirname = Mock()

        exists_call.return_value = False
        dirname_call.return_value = dest_dir
        path_call.return_value = path_mock
        path_mock.mkdir = mkdir_mock

        cleanup_generated_jobs_dir()

        dirname_call.assert_called_with(GENERATED_CONFIGS_DIR)
        path_call.assert_called_with(dest_dir)
        mkdir_mock.assert_called_with(parents=True, exist_ok=True)

    @patch('znoyder.generator.Path', autospec=True)
    def test_generated_config_dir_is_deleted(self, path_call):
        dest_dir = 'path/to/dest/dir'

        path_mock = Mock()
        mkdir_mock = Mock()

        exists_call = znoyder.generator.os.path.exists = Mock()
        dirname_call = znoyder.generator.os.path.dirname = Mock()
        rmtree_call = znoyder.generator.rmtree = Mock()

        exists_call.return_value = True
        dirname_call.return_value = dest_dir
        path_call.return_value = path_mock
        path_mock.mkdir = mkdir_mock

        cleanup_generated_jobs_dir()

        rmtree_call.assert_called_with(GENERATED_CONFIGS_DIR)
