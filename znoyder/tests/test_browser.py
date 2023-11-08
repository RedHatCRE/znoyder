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
import builtins
import logging
from unittest import TestCase
from unittest.mock import Mock, patch

import znoyder.browser
from znoyder.browser import INFO_FILE
from znoyder.browser import RDOINFO_GIT_URL
from znoyder.browser import get_components
from znoyder.browser import get_distroinfo
from znoyder.browser import get_packages
from znoyder.browser import get_projects_mapping
from znoyder.browser import get_releases
from znoyder.browser import main


def setUpModule() -> None:
    logging.disable(logging.CRITICAL)


def tearDownModule() -> None:
    logging.disable(logging.NOTSET)


def days_to_seconds(days):
    return days * 24 * 60 * 60


class TestGetDistroInfo(TestCase):
    def test_correct_params_are_provided(self):
        znoyder.browser.di.DistroInfo = Mock()

        get_distroinfo()

        znoyder.browser.di.DistroInfo.assert_called_with(
            info_files=INFO_FILE,
            cache_ttl=days_to_seconds(1),
            remote_git_info=RDOINFO_GIT_URL
        )

    def test_expected_answer_is_returned(self):
        info = Mock()

        info_call = znoyder.browser.di.DistroInfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get_info = Mock()
        info_call.return_value.get_info.return_value = info

        self.assertEqual(info, get_distroinfo())


class TestComponents(TestCase):
    def test_no_args(self):
        components = [{'name': 'comp_1'}, {'name': 'comp_2'}]

        info_call = znoyder.browser.get_distroinfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get = Mock()
        info_call.return_value.get.return_value = components

        self.assertEqual(components, get_components())

        info_call.return_value.get.assert_called_with('components')

    def test_search_by_name(self):
        components = [{'name': 'comp_1'}, {'name': 'comp_2'}]

        info_call = znoyder.browser.get_distroinfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get = Mock()
        info_call.return_value.get.return_value = components

        self.assertEqual(
            [components[0]],
            get_components(name=components[0]['name'])
        )


class TestGetPackages(TestCase):
    def test_no_args(self):
        project = 'some/project'

        packages = [
            {
                'osp-name': 'pack_1',
                'osp-project': '',
                'osp-patches': 'http://localhost:8080/%s' % project
            }
        ]

        info_call = znoyder.browser.get_distroinfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get = Mock()
        info_call.return_value.get.return_value = packages

        self.assertEqual(packages, get_packages())
        self.assertEqual(project, get_packages()[0]['osp-project'])

    def test_search_by_component(self):
        package1 = {
            'osp-name': 'pack_1',
            'osp-project': '',
            'osp-patches': 'http://localhost:8080/',
            'component': 'comp_1'
        }

        package2 = {
            'osp-name': 'pack_2',
            'osp-project': '',
            'osp-patches': 'http://localhost:8080/',
            'component': 'comp_2'
        }

        packages = [package1, package2]

        info_call = znoyder.browser.get_distroinfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get = Mock()
        info_call.return_value.get.return_value = packages

        self.assertEqual(
            [package1],
            get_packages(component=package1['component'])
        )

    def test_search_by_name(self):
        package1 = {
            'name': 'name_1',
            'osp-name': 'pack_1',
            'osp-project': 'repo_name_1',
            'osp-patches': 'http://localhost:8080/repo_name_1',
            'project': 'project_1',
        }

        package2 = {
            'name': 'name_2',
            'osp-name': 'pack_2',
            'osp-project': 'repo_name_2',
            'osp-patches': 'http://localhost:8080/repo_name_2',
            'project': 'project_2',
        }

        packages = [package1, package2]

        info_call = znoyder.browser.get_distroinfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get = Mock()
        info_call.return_value.get.return_value = packages

        self.assertEqual(
            [package1],
            get_packages(name=package1['name'])
        )

    def test_search_by_osp_name(self):
        package1 = {
            'name': 'name_1',
            'osp-name': 'pack_1',
            'osp-project': 'repo_name_1',
            'osp-patches': 'http://localhost:8080/repo_name_1',
            'project': 'project_1',
        }

        package2 = {
            'name': 'name_2',
            'osp-name': 'pack_2',
            'osp-project': 'repo_name_2',
            'osp-patches': 'http://localhost:8080/repo_name_2',
            'project': 'project_2',
        }

        packages = [package1, package2]

        info_call = znoyder.browser.get_distroinfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get = Mock()
        info_call.return_value.get.return_value = packages

        self.assertEqual(
            [package1],
            get_packages(osp_name=package1['osp-name'])
        )

    def test_search_by_osp_project(self):
        package1 = {
            'name': 'name_1',
            'osp-name': 'pack_1',
            'osp-project': 'repo_name_1',
            'osp-patches': 'http://localhost:8080/repo_name_1',
            'project': 'project_1',
        }

        package2 = {
            'name': 'name_2',
            'osp-name': 'pack_2',
            'osp-project': 'repo_name_2',
            'osp-patches': 'http://localhost:8080/repo_name_2',
            'project': 'project_2',
        }

        packages = [package1, package2]

        info_call = znoyder.browser.get_distroinfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get = Mock()
        info_call.return_value.get.return_value = packages

        self.assertEqual(
            [package1],
            get_packages(osp_project=package1['osp-project'])
        )

    def test_search_by_project(self):
        package1 = {
            'name': 'name_1',
            'osp-name': 'pack_1',
            'osp-project': 'repo_name_1',
            'osp-patches': 'http://localhost:8080/repo_name_1',
            'project': 'project_1',
        }

        package2 = {
            'name': 'name_2',
            'osp-name': 'pack_2',
            'osp-project': 'repo_name_2',
            'osp-patches': 'http://localhost:8080/repo_name_2',
            'project': 'project_2',
        }

        packages = [package1, package2]

        info_call = znoyder.browser.get_distroinfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get = Mock()
        info_call.return_value.get.return_value = packages

        self.assertEqual(
            [package1],
            get_packages(project=package1['project'])
        )

    def test_search_by_tag(self):
        package1 = {
            'osp-name': 'pack_1',
            'osp-project': '',
            'osp-patches': 'http://localhost:8080/',
            'tags': ['tag1']
        }

        package2 = {
            'osp-name': 'pack_2',
            'osp-project': '',
            'osp-patches': 'http://localhost:8080/',
            'tags': ['tag2']
        }

        packages = [package1, package2]

        info_call = znoyder.browser.get_distroinfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get = Mock()
        info_call.return_value.get.return_value = packages

        self.assertEqual(
            [package1],
            get_packages(tag=package1['tags'][0])
        )

    def test_search_by_upstream(self):
        package1 = {
            'osp-name': 'pack_1',
            'osp-project': '',
            'osp-patches': 'http://localhost:8080/',
            'upstream': 'upstream_1'
        }

        package2 = {
            'osp-name': 'pack_2',
            'osp-project': '',
            'osp-patches': 'http://localhost:8080/',
            'upstream': 'upstream_2'
        }

        packages = [package1, package2]

        info_call = znoyder.browser.get_distroinfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get = Mock()
        info_call.return_value.get.return_value = packages

        self.assertEqual(
            [package1],
            get_packages(upstream=package1['upstream'])
        )


class TestProjectsMapping(TestCase):
    def test_happy_path(self):
        args = {'some': 'arg'}

        pkgs_call = znoyder.browser.get_packages = Mock()
        pkgs_call.return_value = []

        self.assertEqual({}, get_projects_mapping(**args))

        pkgs_call.assert_called_with(**args)

    def test_no_upstream_on_pkg(self):
        pkg1_name = 'pack_1'

        packages = [
            {
                'name': pkg1_name
            }
        ]

        pkgs_call = znoyder.browser.get_packages = Mock()
        pkgs_call.return_value = packages

        self.assertEqual(pkg1_name, get_projects_mapping()[pkg1_name])

    def test_upstream_on_pkg(self):
        pkg1_project = 'my/project'
        pkg1_upstream = pkg1_project.replace('/', '-')

        packages = [
            {
                'upstream': 'http://localhost:8080/%s' % pkg1_project
            }
        ]

        pkgs_call = znoyder.browser.get_packages = Mock()
        pkgs_call.return_value = packages

        self.assertEqual(
            pkg1_upstream,
            get_projects_mapping()[pkg1_upstream]
        )

    def test_patches_on_pkg(self):
        pkg1_name = 'pack_1'
        pkg1_patches = 'my/patch'

        packages = [
            {
                'name': pkg1_name,
                'osp-patches': 'http://localhost:8080/%s' % pkg1_patches
            }
        ]

        pkgs_call = znoyder.browser.get_packages = Mock()
        pkgs_call.return_value = packages

        self.assertEqual(
            pkg1_patches,
            get_projects_mapping()[pkg1_name]
        )


class TestGetReleases(TestCase):
    def test_happy_path(self):
        releases = [{'key_1': 'val_1'}]

        info_call = znoyder.browser.get_distroinfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get = Mock()
        info_call.return_value.get.return_value = releases

        self.assertEqual(
            releases,
            get_releases()
        )

        info_call.return_value.get.assert_called_with('osp_releases')

    def test_search_by_tag(self):
        tag1 = 'tag_1'
        tag2 = 'tag_2'

        release1 = {
            'ospinfo_tag_name': [tag1]
        }

        release2 = {
            'ospinfo_tag_name': [tag2]
        }

        releases = [release1, release2]

        info_call = znoyder.browser.get_distroinfo = Mock()

        info_call.return_value = Mock()
        info_call.return_value.get = Mock()
        info_call.return_value.get.return_value = releases

        self.assertEqual(
            [release1],
            get_releases(tag=tag1)
        )


class TestMain(TestCase):
    def test_happy_path(self):
        args = Mock()
        print_call = builtins.print = Mock()

        args.subcommand = None
        args.debug = False
        args.output = False
        args.header = False

        main(args)

        print_call.assert_not_called()

    def test_components_subcommand(self):
        component = {'name': 'comp_1'}

        results = [component]

        args = Mock()
        print_call = builtins.print = Mock()
        components_call = znoyder.browser.get_components = Mock()

        args.subcommand = 'components'
        args.debug = False
        args.output = False
        args.header = False

        components_call.return_value = results

        main(args)

        print_call.assert_called_with(component['name'])

    def test_packages_subcommand(self):
        package = {
            'osp-name': 'pack_1',
            'osp-distgit': 'git_1',
            'osp-patches': 'patch_1'
        }

        results = [package]

        args = Mock()
        print_call = builtins.print = Mock()
        packages_call = znoyder.browser.get_packages = Mock()

        args.subcommand = 'packages'
        args.debug = False
        args.output = False
        args.header = False

        packages_call.return_value = results

        main(args)

        print_call.assert_called_with(
            '%s %s %s' %
            (
                package['osp-name'],
                package['osp-distgit'],
                package['osp-patches']
            )
        )

    def test_releases_subcommand(self):
        release = {
            'ospinfo_tag_name': 'tag_1',
            'git_release_branch': 'branch_1'
        }

        results = [release]

        args = Mock()
        print_call = builtins.print = Mock()
        releases_call = znoyder.browser.get_releases = Mock()

        args.subcommand = 'releases'
        args.debug = False
        args.output = False
        args.header = False

        releases_call.return_value = results

        main(args)

        print_call.assert_called_with(
            '%s %s' %
            (
                release['ospinfo_tag_name'],
                release['git_release_branch']
            )
        )

    @patch('pprint.PrettyPrinter.pprint')
    def test_debug_mode(self, print_call):
        args = Mock()

        args.subcommand = None
        args.debug = True
        args.output = False
        args.header = False

        main(args)

        print_call.assert_called_with(None)

    def test_output_mode(self):
        output1 = 'output1'
        output2 = 'output2'

        component = {
            'name': 'comp_1',
            output1: 'val_1',
            output2: 'val_2'
        }

        results = [component]

        args = Mock()
        print_call = builtins.print = Mock()
        components_call = znoyder.browser.get_components = Mock()

        args.subcommand = 'components'
        args.debug = False
        args.output = '%s,%s' % (output1, output2)
        args.header = False

        components_call.return_value = results

        main(args)

        print_call.assert_called_with(
            '%s %s' % (component[output1], component[output2])
        )

    def test_header_mode(self):
        output1 = 'output1'
        output2 = 'output2'

        args = Mock()
        print_call = builtins.print = Mock()

        args.subcommand = None
        args.debug = False
        args.output = '%s,%s' % (output1, output2)
        args.header = True

        main(args)

        print_call.assert_any_call(
            '%s %s' % (output1, output2)
        )

        print_call.assert_any_call(
            '%s %s' % ('-' * len(output1), '-' * len(output2))
        )
