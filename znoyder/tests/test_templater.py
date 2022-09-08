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

import textwrap
from unittest import TestCase
from unittest.mock import mock_open
from unittest.mock import patch

from znoyder.lib.logger import LOG
from znoyder.templater import generate_zuul_project_template
from znoyder.templater import generate_zuul_projects_config
from znoyder.templater import generate_zuul_resources_config
from znoyder.templater import main


class TestTemplater(TestCase):
    @patch('znoyder.templater.open', new_callable=mock_open())
    def test_generate_zuul_project_template(self, mock_file):
        path = 'some/file/and.extension'
        name = 'test'
        pipelines = {
            'check': [
                {
                    'name': 'job1',
                    'branch': 'branch1',
                    'parameters': {},
                    'voting': 'true',
                },
                {
                    'name': 'job2',
                    'branch': 'branch2',
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
        }

        expected = textwrap.dedent('''
            ---
            - project-template:
                name: test
                check:
                  jobs:
                    - job1:
                        branches: branch1
                        voting: true
                    - job2:
                        branches: branch2
                        voting: false
                gate:
                  jobs:
                    - job3:
                        branches: branch1
                        voting: true
            ''').strip()

        generate_zuul_project_template(path, name, pipelines)

        mock_file.assert_called_once_with(path, 'w')
        mock_write = mock_file.return_value.__enter__().write
        mock_write.assert_any_call(expected)
        mock_write.assert_any_call('\n')
        self.assertEqual(mock_write.call_count, 2)

    @patch('znoyder.templater.open', new_callable=mock_open())
    def test_generate_zuul_projects_config(self, mock_file):
        path = 'some/file/and.extension'
        projects = ['project1', 'project2']
        prefix = 'test-'

        expected = textwrap.dedent('''
            ---
            - project:
                name: project1
                templates:
                  - test-project1
                vars:
                  test_setup_skip: true

            - project:
                name: project2
                templates:
                  - test-project2
                vars:
                  test_setup_skip: true
            ''').strip()

        generate_zuul_projects_config(path, projects, prefix)

        mock_file.assert_called_once_with(path, 'w')
        mock_write = mock_file.return_value.__enter__().write
        mock_write.assert_any_call(expected)
        mock_write.assert_any_call('\n')
        self.assertEqual(mock_write.call_count, 2)

    @patch('znoyder.templater.open', new_callable=mock_open())
    def test_generate_zuul_resources_config(self, mock_file):
        path = 'some/file/and.extension'
        projects = ['project1', 'project2']
        prefix = 'test-'

        expected = textwrap.dedent('''
            ---
            resources:
               tenants:
                  osp-internal:
                     description: OSP Internal tenant – hosting Component CI jobs
                     url: https://sf.hosted.upshift.rdu2.redhat.com/manage
                     default-connection: code.engineering.redhat.com
                     tenant-options:
                        zuul/max-job-timeout: 21600
                        zuul/web-root: https://sf.hosted.upshift.rdu2.redhat.com/zuul/t/osp-internal/
                        zuul/report-build-page: true

               projects:
                  osp-internal:
                     tenant: osp-internal
                     description: OSP Internal tenant – hosting Component CI jobs
                     contacts:
                       - rhos-cre@redhat.com
                     source-repositories:
                       - project1:
                           zuul/include: []
                           repoxplorer/skip: true
                           hound/skip: true
                       - project2:
                           zuul/include: []
                           repoxplorer/skip: true
                           hound/skip: true
                       - zuul/zuul-jobs:
                           connection: opendev.org
                           repoxplorer/skip: true
                           hound/skip: true
                       - osp-dfg-compute/segritary:
                           zuul/config-project: True
                           connection: gitlab.cee
                           repoxplorer/skip: true
                           hound/skip: true
            ''').strip()  # noqa: E501 (line too long)

        generate_zuul_resources_config(path, projects, prefix)

        mock_file.assert_called_once_with(path, 'w')
        mock_write = mock_file.return_value.__enter__().write
        mock_write.assert_any_call(expected)
        mock_write.assert_any_call('\n')
        self.assertEqual(mock_write.call_count, 2)

    def test_main(self):
        with self.assertLogs(LOG) as mock_log:
            expected = [
                'INFO:znoyderLogger:Available templates:',
                'INFO:znoyderLogger:   - zuul-project-template',
                'INFO:znoyderLogger:   - zuul-projects-config',
                'INFO:znoyderLogger:   - zuul-resources',
            ]

            main(None)

            self.assertEqual(len(mock_log.records), 4)
            self.assertEqual(mock_log.output, expected)
