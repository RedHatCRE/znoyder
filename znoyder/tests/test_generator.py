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
from znoyder.generator import cleanup_generated_jobs_dir
from znoyder.generator import fetch_osp_projects
from znoyder.generator import list_existing_osp_projects


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
