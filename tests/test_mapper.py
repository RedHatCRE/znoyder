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

from unittest import TestCase
from unittest.mock import Mock

from znoyder.mapper import add_map
from znoyder.mapper import add_jobs
from znoyder.mapper import copy_map
from znoyder.mapper import copy_jobs
from znoyder.mapper import exclude_map
from znoyder.mapper import exclude_jobs
from znoyder.mapper import match
from znoyder.mapper import override_map
from znoyder.mapper import override_jobs
from znoyder.lib.zuul import ZuulJob


class TestMatcher(TestCase):
    def test_match(self):
        self.assertTrue(match('foobar', 'foobar'))
        self.assertFalse(match('foobar', 'foo'))
        self.assertTrue(match('foobar', '/foo/'))


class TestJobsGeneratorFromMapEntry(TestCase):
    def setUp(self) -> None:
        add_map.clear()

    def test_job_generation_without_type(self):
        job_name = 'job_1'
        job_options = {'opt_1': 'val_1'}

        add_map.update({
            '/.*/': {
                '/.*/': {
                    job_name: job_options
                }
            }
        })

        result = add_jobs([], 'any', 'any')[0]

        self.assertIsInstance(result, ZuulJob)

        self.assertEqual(job_name, result.job_name)
        self.assertEqual('check', result.job_trigger_type)
        self.assertEqual(job_options, result.job_data)

    def test_job_generation_with_type(self):
        job_name = 'job_1'
        job_type = 'type'
        job_options = {'opt_1': 'val_1'}

        add_map.update({
            '/.*/': {
                '/.*/': {
                    job_name: {'type': job_type} | job_options
                }
            }
        })

        result = add_jobs([], 'any', 'any')[0]

        self.assertIsInstance(result, ZuulJob)

        self.assertEqual(job_name, result.job_name)
        self.assertEqual(job_type, result.job_trigger_type)
        self.assertEqual(job_options, result.job_data)


class TestExcludeJobs(TestCase):
    def setUp(self) -> None:
        exclude_map.clear()

    def test_happy_path(self):
        self.assertEqual([], exclude_jobs([], 'any', 'any'))

    def test_exclude_by_name(self):
        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        exclude_map.update({
            '/.*/': {
                '/.*/': {
                    job2.job_name: ''
                }
            }
        })

        self.assertEqual([job1], exclude_jobs([job1, job2], 'any', 'any'))

    def test_exclude_by_tag(self):
        tag = 'tag_1'

        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        exclude_map.update({
            '/.*/': {
                tag: {
                    job2.job_name: ''
                }
            }
        })

        self.assertEqual([job1], exclude_jobs([job1, job2], 'any', tag))

    def test_exclude_by_tag_and_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        exclude_map.update({
            project: {
                tag: {
                    job2.job_name: ''
                }
            }
        })

        self.assertEqual([job1], exclude_jobs([job1, job2], project, tag))


class TestAddJobs(TestCase):
    def setUp(self) -> None:
        add_map.clear()

    def test_happy_path(self):
        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        jobs = [job1, job2]

        result = add_jobs(jobs, 'any', 'any')

        for i, _ in enumerate(result):
            self.assertEqual(jobs[i].job_name, result[i].job_name)

    def test_add_by_name(self):
        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        jobs = [job1]

        add_map.update({
            '/.*/': {
                '/.*/': {
                    job2.job_name: {}
                }
            }
        })

        result = add_jobs(jobs, 'any', 'any')

        for i, _ in enumerate(result):
            self.assertEqual([job1, job2][i].job_name, result[i].job_name)

    def test_add_by_tag(self):
        tag = 'tag_1'

        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        jobs = [job1]

        add_map.update({
            '/.*/': {
                tag: {
                    job2.job_name: {}
                }
            }
        })

        result = add_jobs(jobs, 'any', tag)

        for i, _ in enumerate(result):
            self.assertEqual([job1, job2][i].job_name, result[i].job_name)

    def test_add_by_tag_and_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        jobs = [job1]

        add_map.update({
            project: {
                tag: {
                    job2.job_name: {}
                }
            }
        })

        result = add_jobs(jobs, project, tag)

        for i, _ in enumerate(result):
            self.assertEqual([job1, job2][i].job_name, result[i].job_name)


class TestOverrideJobs(TestCase):
    def setUp(self) -> None:
        override_map.clear()

    def test_happy_path(self):
        self.assertEqual([], override_jobs([], 'any', 'any'))

    def test_override_by_name(self):
        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        job_data = {'voting': True}

        jobs = [job1, job2]

        override_map.update({
            '/.*/': {
                '/.*/': {
                    job2.job_name: job_data
                }
            }
        })

        override_jobs(jobs, 'any', 'any')

        self.assertNotIsInstance(job1.job_data, type(job_data))
        self.assertIsInstance(job2.job_data, type(job_data))
        self.assertEqual(job2.job_data, job_data)

    def test_override_by_tag(self):
        tag = 'tag_1'

        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        job_data = {'voting': True}

        jobs = [job1, job2]

        override_map.update({
            '/.*/': {
                tag: {
                    job2.job_name: job_data
                }
            }
        })

        override_jobs(jobs, 'any', tag)

        self.assertNotIsInstance(job1.job_data, type(job_data))
        self.assertIsInstance(job2.job_data, type(job_data))
        self.assertEqual(job2.job_data, job_data)

    def test_override_by_tag_and_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = Mock()
        job2 = Mock()

        job1.job_name = 'job_1'
        job2.job_name = 'job_2'

        job_data = {'voting': True}

        jobs = [job1, job2]

        override_map.update({
            project: {
                tag: {
                    job2.job_name: job_data
                }
            }
        })

        override_jobs(jobs, project, tag)

        self.assertNotIsInstance(job1.job_data, type(job_data))
        self.assertIsInstance(job2.job_data, type(job_data))
        self.assertEqual(job2.job_data, job_data)


class TestCopyJobs(TestCase):
    def setUp(self) -> None:
        copy_map.clear()

    def test_happy_path(self):
        self.assertEqual([], copy_jobs([], 'any', 'any'))

    pass  # TODO(sdatko): implement
