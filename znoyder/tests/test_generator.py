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

import os.path
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

from yaml.parser import ParserError

from znoyder.config import extra_projects
from znoyder.config import UPSTREAM_CONFIGS_DIR
from znoyder.generator import cache
from znoyder.generator import cleanup_generated_jobs_dir
from znoyder.generator import fetch_templates_directory
from znoyder.generator import fetch_osp_projects
from znoyder.generator import discover_jobs
from znoyder.generator import generate_projects_pipelines_dict
from znoyder.generator import generate_projects_templates
from znoyder.generator import generate_projects_config
from znoyder.generator import generate_resources_config
from znoyder.generator import main
from znoyder.lib.logger import LOG
from znoyder.lib.zuul import ZuulJob


class TestGenerator(TestCase):
    def setUp(self) -> None:
        cache.clear()

        self.example_projects_pipelines_dict = {
            'project1': {
                'check': [
                    {
                        'name': 'job1',
                        'branch': 'branch1',
                        'parameters': {},
                        'voting': 'true',
                    },
                    {
                        'name': 'job2',
                        'branch': 'branch1',
                        'parameters': {},
                        'voting': 'false',
                    },
                ],
                'gate': [
                    {
                        'name': 'job3',
                        'branch': 'branch1',
                        'parameters': {},
                        'voting': 'true',
                    },
                ],
            },
            'project2': {
                'check': [
                    {
                        'name': 'job4',
                        'branch': 'branch1',
                        'parameters': {},
                        'voting': 'true',
                    },
                    {
                        'name': 'job5',
                        'branch': 'branch1',
                        'parameters': {},
                        'voting': 'false',
                    },
                ],
            },
            'project3': {
            },
        }

    @patch('pathlib.Path.mkdir')
    @patch('znoyder.generator.rmtree')
    @patch('os.path.exists', return_value=False)
    def test_cleanup_generated_jobs_dir_not_exists(self, mock_exists,
                                                   mock_rmtree, mock_mkdir):
        cleanup_generated_jobs_dir()

        mock_exists.assert_called_once()
        mock_rmtree.assert_not_called()
        self.assertEqual(mock_mkdir.call_count, 3)

    @patch('pathlib.Path.mkdir')
    @patch('znoyder.generator.rmtree')
    @patch('os.path.exists', return_value=True)
    def test_cleanup_generated_jobs_dir_exists(self, mock_exists,
                                               mock_rmtree, mock_mkdir):
        with self.assertLogs(LOG) as mock_log:
            cleanup_generated_jobs_dir()

        expected_log = [
            'INFO:znoyderLogger:Removed the directory: files-generated/',
        ]
        self.assertEqual(len(mock_log.records), 1)
        self.assertEqual(mock_log.output, expected_log)

        mock_exists.assert_called_once()
        mock_rmtree.assert_called_once()
        self.assertEqual(mock_mkdir.call_count, 3)

    @patch('znoyder.downloader.download_zuul_config')
    def test_fetch_templates_directory(self, mock_downloader):
        mock_downloader.return_value = {
            'organization/repository': ['url-to-yaml-file']
        }

        templates_directory = fetch_templates_directory()

        mock_downloader.assert_called_once_with(
            repository='https://opendev.org/openstack/openstack-zuul-jobs',
            branch='master',
            destination='files-upstream/',
            errors_fatal=False,
            skip_existing=True,
        )
        self.assertEqual(templates_directory, 'organization/repository')

    @patch('znoyder.downloader.download_zuul_config')
    @patch('znoyder.browser.get_packages')
    def test_fetch_osp_projects(self, mock_browser, mock_downloader):
        extra_projects.clear()
        extra_projects.update({'additional-project': 'url-to-additional-repo'})

        mock_browser.return_value = [
            {
                'osp-project': 'project1',
                'upstream': 'url1',
                'tag': 'tag1',
            },
            {
                'osp-project': 'project2',
                'upstream': 'url2',
                'tag': 'tag1',
            },
            {
                'osp-project': 'project3',
                'upstream': 'url3',
                'tag': 'tag3',
            },
        ]
        mock_downloader.side_effect = [
            {'organization/repository1': ['url-to-yaml-file1']},
            {'organization/repository2': ['url-to-yaml-file2']},
            {'organization/repository3': ['url-to-yaml-file3']},
            {'additional/project1': ['url-to-yaml-file4']},
        ]

        projects = fetch_osp_projects('any-tag', {})

        self.assertEqual({'project1': 'any-tag/organization/repository1',
                          'project2': 'any-tag/organization/repository2',
                          'project3': 'any-tag/organization/repository3',
                          'additional-project': 'any-tag/additional/project1'},
                         projects)

    @patch('znoyder.mapper.copy_jobs')
    @patch('znoyder.mapper.override_jobs')
    @patch('znoyder.mapper.add_jobs')
    @patch('znoyder.mapper.exclude_jobs')
    @patch('znoyder.mapper.include_jobs')
    @patch('znoyder.finder.find_jobs')
    @patch('os.path.exists', return_value=True)
    def test_discover_jobs(self, mock_exists, mock_finder,
                           mock_include, mock_exclude,
                           mock_add, mock_override, mock_copy):
        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')
        job3 = ZuulJob('job3', 'check')

        mock_finder.return_value = [1]  # Values do not matter here
        mock_include.return_value = [2]  # as the mapper is tested
        mock_exclude.return_value = [3]  # in a separate module, hence
        mock_add.return_value = [4]  # here we just assume any output
        mock_override.return_value = [5]  # to ensure the execution order
        mock_copy.return_value = [job1, job2, job3]

        project_name = 'project1'
        tag = 'any-tag'
        directory = 'example/path'
        templates = ['templates']
        pipelines = ['pipelines']

        with self.assertLogs(LOG) as mock_log:
            jobs = discover_jobs(project_name, tag, directory,
                                 templates, pipelines)

        expected_log = [
            'INFO:znoyderLogger:Including from: example/path',
            'INFO:znoyderLogger:Jobs number: 3',
        ]
        self.assertEqual(len(mock_log.records), 2)
        self.assertEqual(mock_log.output, expected_log)

        expected_dir = os.path.abspath(os.path.join(UPSTREAM_CONFIGS_DIR,
                                                    directory))

        mock_exists.assert_called_once_with(expected_dir)
        mock_finder.assert_called_once_with(expected_dir, templates, pipelines)
        mock_include.assert_called_once_with([1], tag)
        mock_exclude.assert_called_once_with([2], project_name, tag)
        mock_add.assert_called_once_with([3], project_name, tag)
        mock_override.assert_called_once_with([4], project_name, tag)
        mock_copy.assert_called_once_with([5], project_name, tag)

        self.assertEqual([job1, job2, job3], jobs)

    @patch('znoyder.generator.discover_jobs')
    @patch('znoyder.finder.find_templates')
    @patch('znoyder.finder.find_pipelines')
    @patch('znoyder.generator.fetch_osp_projects')
    @patch('znoyder.generator.fetch_templates_directory')
    @patch('znoyder.generator.branches_map')
    def test_generate_projects_pipelines_dict(self,
                                              mock_branches_map,
                                              mock_gen_templates,
                                              mock_gen_projects,
                                              mock_find_pipelines,
                                              mock_find_templates,
                                              mock_discover_jobs):
        args = Mock()
        args.tag = 'tag1,tag2'
        args.component = None
        args.name = None
        args.osp_name = None
        args.osp_project = None
        args.project = None

        mock_branches_map.get.return_value = {'upstream': 'upstream1',
                                              'downstream': 'branch1'}
        mock_gen_templates.return_value = 'organization/templates'
        mock_gen_projects.side_effect = [
            # tag1
            {'project1': 'upstream1/organization/repository1',
             'project2': 'upstream1/organization/repository2',
             'project3': 'upstream1/organization/repository3'},
            # tag2
            {}
        ]

        job0 = ZuulJob('template-job', 'check')
        job1 = ZuulJob('job1', 'check', {'voting': 'true'})
        job2 = ZuulJob('job2', 'check')
        job3 = ZuulJob('job3', 'gate', {'voting': 'true'})
        job4 = ZuulJob('job4', 'check', {'voting': 'true'})
        job5 = ZuulJob('job5', 'check')

        mock_find_pipelines.return_value = ['check', 'gate']
        mock_find_templates.return_value = [job0]

        mock_discover_jobs.side_effect = [
            [job1, job2, job3],
            [job4, job5],
            [],
        ]

        with self.assertLogs(LOG) as mock_log:
            actual = generate_projects_pipelines_dict(args)

        # Replace defaultdicts with regular dicts for comparison
        actual = {project_name: dict(actual[project_name])
                  for project_name in actual}
        expected = self.example_projects_pipelines_dict
        self.assertDictEqual(actual, expected)

        expected_log = [
            ('INFO:znoyderLogger:Downloading Zuul configuration'
             ' from upstream...'),
            'INFO:znoyderLogger:Zuul configuration files: files-upstream/',
            ('INFO:znoyderLogger:Generating new downstream'
             ' configuration files...'),
            'INFO:znoyderLogger:Output path: files-generated/',
            ('INFO:znoyderLogger:Processing: project1'
             ' (upstream1/organization/repository1)'),
            ('INFO:znoyderLogger:Processing: project2'
             ' (upstream1/organization/repository2)'),
            ('INFO:znoyderLogger:Processing: project3'
             ' (upstream1/organization/repository3)'),
            ('INFO:znoyderLogger:Downloading Zuul configuration'
             ' from upstream...'),
            'INFO:znoyderLogger:Zuul configuration files: files-upstream/',
            ('WARNING:znoyderLogger:Did not find any projects'
             ' using following filters: {\'tag\': \'tag2\'}.'),
        ]
        self.assertEqual(len(mock_log.records), 10)
        self.assertEqual(mock_log.output, expected_log)

    @patch('znoyder.generator.fetch_osp_projects')
    @patch('znoyder.generator.fetch_templates_directory')
    @patch('znoyder.generator.branches_map')
    def test_generate_projects_pipelines_dict_no_projects(self,
                                                          mock_branches_map,
                                                          mock_gen_templates,
                                                          mock_gen_projects):
        args = Mock()
        args.tag = None
        args.component = 'any1'
        args.name = 'any2'
        args.osp_name = 'any3'
        args.osp_project = 'any4'
        args.project = 'any5'

        mock_branches_map.keys.return_value = {'tag2'}
        mock_branches_map.get.return_value = {'upstream': 'non-relevant',
                                              'downstream': 'branch1'}
        mock_gen_templates.return_value = 'organization/templates'
        mock_gen_projects.return_value = {}

        with self.assertLogs(LOG) as mock_log:
            actual = generate_projects_pipelines_dict(args)

        # Replace defaultdicts with regular dicts for comparison
        actual = {project_name: dict(actual[project_name])
                  for project_name in actual}
        expected = {}
        self.assertDictEqual(actual, expected)

        expected_log = [
            ('INFO:znoyderLogger:Downloading Zuul configuration'
             ' from upstream...'),
            'INFO:znoyderLogger:Zuul configuration files: files-upstream/',
            ('WARNING:znoyderLogger:Did not find any projects'
             ' using following filters: {\'tag\': \'tag2\','
             ' \'component\': \'any1\', \'name\': \'any2\','
             ' \'osp_name\': \'any3\', \'osp_project\': \'any4\','
             ' \'project\': \'any5\'}.'),
        ]
        self.assertEqual(len(mock_log.records), 3)
        self.assertEqual(mock_log.output, expected_log)

    @patch('znoyder.templater.generate_zuul_project_template')
    def test_generate_projects_templates(self, mock_templater):
        with self.assertLogs(LOG) as mock_log:
            generate_projects_templates(self.example_projects_pipelines_dict)

        expected_log = [
            'INFO:znoyderLogger:Writing '
            'files-generated/osp-internal-jobs/zuul.d/cre-project1.yaml',
            'INFO:znoyderLogger:Writing '
            'files-generated/osp-internal-jobs/zuul.d/cre-project2.yaml',
            'INFO:znoyderLogger:Writing '
            'files-generated/osp-internal-jobs/zuul.d/cre-project3.yaml',
        ]
        self.assertEqual(len(mock_log.records), 3)
        self.assertEqual(mock_log.output, expected_log)

        self.assertEqual(mock_templater.call_count, 3)
        mock_templater.assert_any_call(
            path='files-generated/osp-internal-jobs/zuul.d/cre-project1.yaml',
            name='cre-project1',
            pipelines={
                'check': [
                    {'name': 'job1', 'branch': 'branch1',
                     'parameters': {}, 'voting': 'true'},
                    {'name': 'job2', 'branch': 'branch1',
                     'parameters': {}, 'voting': 'false'}
                ],
                'gate': [
                    {'name': 'job3', 'branch': 'branch1',
                     'parameters': {}, 'voting': 'true'}
                ]
            }
        )
        mock_templater.assert_any_call(
            path='files-generated/osp-internal-jobs/zuul.d/cre-project2.yaml',
            name='cre-project2',
            pipelines={
                'check': [
                    {'name': 'job4', 'branch': 'branch1',
                     'parameters': {}, 'voting': 'true'},
                    {'name': 'job5', 'branch': 'branch1',
                     'parameters': {}, 'voting': 'false'}
                ]
            }
        )
        mock_templater.assert_any_call(
            path='files-generated/osp-internal-jobs/zuul.d/cre-project3.yaml',
            name='cre-project3',
            pipelines={}
        )

    @patch('znoyder.templater.generate_zuul_project_template')
    def test_generate_projects_templates_exception(self, mock_templater):
        mock_templater.side_effect = ParserError()

        with self.assertLogs(LOG) as mock_log, self.assertRaises(ParserError):
            generate_projects_templates(self.example_projects_pipelines_dict)

        expected_log = [
            'INFO:znoyderLogger:Writing '
            'files-generated/osp-internal-jobs/zuul.d/cre-project1.yaml',
            'ERROR:znoyderLogger:Problem processing project1',
        ]
        self.assertEqual(len(mock_log.records), 2)
        self.assertEqual(mock_log.output, expected_log)

    @patch('znoyder.templater.generate_zuul_projects_config')
    def test_generate_projects_config(self, mock_templater):
        with self.assertLogs(LOG) as mock_log:
            generate_projects_config(self.example_projects_pipelines_dict)

        expected_log = [
            'INFO:znoyderLogger:Writing '
            'files-generated/osp-internal-jobs-config/zuul.d/cre-projects.yaml'
        ]
        self.assertEqual(len(mock_log.records), 1)
        self.assertEqual(mock_log.output, expected_log)

        mock_templater.assert_called_once_with(
            path='files-generated/osp-internal-jobs-config/'
                 'zuul.d/cre-projects.yaml',
            projects=['project1', 'project2', 'project3'],
            prefix='cre-',
        )

    @patch('znoyder.templater.generate_zuul_resources_config')
    def test_generate_resources_config(self, mock_templater):
        with self.assertLogs(LOG) as mock_log:
            generate_resources_config(self.example_projects_pipelines_dict)

        expected_log = [
            'INFO:znoyderLogger:Writing '
            'files-generated/sf-config/resources/osp-internal.yaml'
        ]
        self.assertEqual(len(mock_log.records), 1)
        self.assertEqual(mock_log.output, expected_log)

        mock_templater.assert_called_once_with(
            path='files-generated/sf-config/resources/osp-internal.yaml',
            projects=['project1', 'project2', 'project3'],
            prefix='cre-',
        )

    @patch('znoyder.generator.cache')
    @patch('znoyder.generator.generate_resources_config')
    @patch('znoyder.generator.generate_projects_config')
    @patch('znoyder.generator.generate_projects_templates')
    @patch('znoyder.generator.generate_projects_pipelines_dict')
    @patch('znoyder.generator.cleanup_generated_jobs_dir')
    def test_main(self, mock_cleanup, mock_gen_dict, mock_gen_templates,
                  mock_gen_projects, mock_gen_resources, mock_cache):
        with self.assertLogs(LOG) as mock_log:
            mock_cache.changed = True
            main(None)

        mock_cache.save.assert_called_once()
        mock_cleanup.assert_called_once()
        mock_gen_dict.assert_called_once()
        mock_gen_templates.assert_called_once()
        mock_gen_projects.assert_called_once()
        mock_gen_resources.assert_called_once()

        expected_log = [
            'INFO:znoyderLogger:Saving cache file'
        ]
        self.assertEqual(len(mock_log.records), 1)
        self.assertEqual(mock_log.output, expected_log)
