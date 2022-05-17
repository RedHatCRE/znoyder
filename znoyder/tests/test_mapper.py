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

import logging
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


logging.disable(logging.CRITICAL)


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
        job_parameters = {'opt_1': 'val_1'}

        add_map.update({
            '/.*/': {
                '/.*/': {
                    job_name: job_parameters
                }
            }
        })

        result = add_jobs([], 'any', 'any')[0]

        self.assertIsInstance(result, ZuulJob)

        self.assertEqual(job_name, result.name)
        self.assertEqual('check', result.pipeline)
        self.assertEqual(job_parameters, result.parameters)

    def test_job_generation_with_type(self):
        job_name = 'job_1'
        job_type = 'type'
        job_parameters = {'opt_1': 'val_1'}

        add_map.update({
            '/.*/': {
                '/.*/': {
                    job_name: {'pipeline': job_type} | job_parameters
                }
            }
        })

        result = add_jobs([], 'any', 'any')[0]

        self.assertIsInstance(result, ZuulJob)

        self.assertEqual(job_name, result.name)
        self.assertEqual(job_type, result.pipeline)
        self.assertEqual(job_parameters, result.parameters)

    def test_job_generation_with_multiple_types(self):
        job_name = 'job_1'
        job_types = ['type1', 'type2']
        job_parameters = {'opt_1': 'val_1'}

        add_map.update({
            '/.*/': {
                '/.*/': {
                    job_name: {'pipeline': job_types} | job_parameters
                }
            }
        })

        result = add_jobs([], 'any', 'any')

        self.assertIsInstance(result, list)

        for i in range(len(job_types)):
            self.assertEqual(job_name, result[i].name)
            self.assertEqual(job_types[i], result[i].pipeline)
            self.assertEqual(job_parameters, result[i].parameters)


class TestExcludeJobs(TestCase):
    def setUp(self) -> None:
        exclude_map.clear()

    def test_happy_path(self):
        self.assertEqual([], exclude_jobs([], 'any', 'any'))

    def test_exclude_by_name(self):
        job1 = Mock()
        job2 = Mock()

        job1.name = 'job_1'
        job2.name = 'job_2'

        exclude_map.update({
            '/.*/': {
                '/.*/': {
                    job2.name: ''
                }
            }
        })

        self.assertEqual([job1], exclude_jobs([job1, job2], 'any', 'any'))

    def test_exclude_by_tag(self):
        tag = 'tag_1'

        job1 = Mock()
        job2 = Mock()

        job1.name = 'job_1'
        job2.name = 'job_2'

        exclude_map.update({
            '/.*/': {
                tag: {
                    job2.name: ''
                }
            }
        })

        self.assertEqual([job1], exclude_jobs([job1, job2], 'any', tag))

    def test_exclude_by_tag_and_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = Mock()
        job2 = Mock()

        job1.name = 'job_1'
        job2.name = 'job_2'

        exclude_map.update({
            project: {
                tag: {
                    job2.name: ''
                }
            }
        })

        self.assertEqual([job1], exclude_jobs([job1, job2], project, tag))

    def test_exclude_skip_unmatched_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = Mock()
        job2 = Mock()

        job1.name = 'job_1'
        job2.name = 'job_2'

        jobs = [job1, job2]

        exclude_map.update({
            project: {
                tag: {
                    job2.name: ''
                }
            }
        })

        exclude_jobs(jobs, 'any', tag)

        self.assertEqual([job1, job2], jobs)

    def test_exclude_skip_unmatched_tag(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = Mock()
        job2 = Mock()

        job1.name = 'job_1'
        job2.name = 'job_2'

        jobs = [job1, job2]

        exclude_map.update({
            project: {
                tag: {
                    job2.name: ''
                }
            }
        })

        exclude_jobs(jobs, project, 'any')

        self.assertEqual([job1, job2], jobs)


class TestAddJobs(TestCase):
    def setUp(self) -> None:
        add_map.clear()

    def test_happy_path(self):
        job1 = Mock()
        job2 = Mock()

        job1.name = 'job_1'
        job2.name = 'job_2'

        jobs = [job1, job2]

        result = add_jobs(jobs, 'any', 'any')

        for i, _ in enumerate(result):
            self.assertEqual(jobs[i].name, result[i].name)

    def test_add_by_name(self):
        job1 = Mock()
        job2 = Mock()

        job1.name = 'job_1'
        job2.name = 'job_2'

        jobs = [job1]

        add_map.update({
            '/.*/': {
                '/.*/': {
                    job2.name: {}
                }
            }
        })

        result = add_jobs(jobs, 'any', 'any')

        for i, _ in enumerate(result):
            self.assertEqual([job1, job2][i].name, result[i].name)

    def test_add_by_tag(self):
        tag = 'tag_1'

        job1 = Mock()
        job2 = Mock()

        job1.name = 'job_1'
        job2.name = 'job_2'

        jobs = [job1]

        add_map.update({
            '/.*/': {
                tag: {
                    job2.name: {}
                }
            }
        })

        result = add_jobs(jobs, 'any', tag)

        for i, _ in enumerate(result):
            self.assertEqual([job1, job2][i].name, result[i].name)

    def test_add_by_tag_and_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = Mock()
        job2 = Mock()

        job1.name = 'job_1'
        job2.name = 'job_2'

        jobs = [job1]

        add_map.update({
            project: {
                tag: {
                    job2.name: {}
                }
            }
        })

        result = add_jobs(jobs, project, tag)

        for i, _ in enumerate(result):
            self.assertEqual([job1, job2][i].name, result[i].name)

    def test_add_skip_unmatched_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = Mock()
        job2 = Mock()

        job1.name = 'job_1'
        job2.name = 'job_2'

        jobs = [job1]

        add_map.update({
            project: {
                tag: {
                    job2.name: {}
                }
            }
        })

        add_jobs(jobs, 'any', tag)

        self.assertEqual(jobs, [job1])

    def test_add_skip_unmatched_tag(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = Mock()
        job2 = Mock()

        job1.name = 'job_1'
        job2.name = 'job_2'

        jobs = [job1]

        add_map.update({
            project: {
                tag: {
                    job2.name: {}
                }
            }
        })

        add_jobs(jobs, project, 'any')

        self.assertEqual(jobs, [job1])


class TestOverrideJobs(TestCase):
    def setUp(self) -> None:
        override_map.clear()

    def test_happy_path(self):
        self.assertEqual([], override_jobs([], 'any', 'any'))

    def test_override_by_name(self):
        job1 = Mock()
        job2 = Mock()

        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')

        job_data = {'voting': True}

        jobs = [job1, job2]

        override_map.update({
            '/.*/': {
                '/.*/': {
                    job2.name: job_data
                }
            }
        })

        override_jobs(jobs, 'any', 'any')

        self.assertDictEqual(job1.parameters, {})
        self.assertTrue(set(job_data).issubset(set(job2.parameters)))

    def test_override_by_tag(self):
        tag = 'tag_1'

        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')

        job_data = {'voting': True}

        jobs = [job1, job2]

        override_map.update({
            '/.*/': {
                tag: {
                    job2.name: job_data
                }
            }
        })

        override_jobs(jobs, 'any', tag)

        self.assertDictEqual(job1.parameters, {})
        self.assertTrue(set(job_data).issubset(set(job2.parameters)))

    def test_override_by_tag_and_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')

        job_data = {'voting': True}

        jobs = [job1, job2]

        override_map.update({
            project: {
                tag: {
                    job2.name: job_data
                }
            }
        })

        override_jobs(jobs, project, tag)

        self.assertDictEqual(job1.parameters, {})
        self.assertTrue(set(job_data).issubset(set(job2.parameters)))

    def test_override_skip_unmatched_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')

        job_data = {'voting': True}

        jobs = [job1, job2]

        override_map.update({
            project: {
                tag: {
                    job2.name: job_data
                }
            }
        })

        override_jobs(jobs, 'any', tag)

        self.assertDictEqual(job1.parameters, {})
        self.assertDictEqual(job2.parameters, {})

    def test_override_skip_unmatched_tag(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')

        job_data = {'voting': True}

        jobs = [job1, job2]

        override_map.update({
            project: {
                tag: {
                    job2.name: job_data
                }
            }
        })

        override_jobs(jobs, project, 'any')

        self.assertDictEqual(job1.parameters, {})
        self.assertDictEqual(job2.parameters, {})

    def test_override_unset_job_option(self):
        tag = 'tag_1'
        project = 'project_1'

        job_data_key = 'voting'
        job_data = {job_data_key: True}

        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check', job_data)

        jobs = [job1, job2]

        override_map.update({
            project: {
                tag: {
                    job2.name: {
                        job_data_key: None
                    }
                }
            }
        })

        override_jobs(jobs, project, tag)

        self.assertDictEqual(job1.parameters, {})
        self.assertDictEqual(job2.parameters, {})
        self.assertFalse(job_data == {})


class TestCopyJobs(TestCase):
    def setUp(self) -> None:
        copy_map.clear()

    def test_happy_path(self):
        self.assertEqual([], copy_jobs([], 'any', 'any'))

    def test_copy_from_to(self):
        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')

        jobs = [job1, job2]

        copy_map.update({
            '/.*/': {
                '/.*/': [{
                    job2.name: {
                        'from': 'check',
                        'to': 'gate',
                        'voting': True
                    }
                }]
            }
        })

        copy_jobs(jobs, 'any', 'any')

        self.assertEqual(len(jobs), 3)
        self.assertTrue(ZuulJob('job1', 'check') in jobs)
        self.assertTrue(ZuulJob('job2', 'check') in jobs)
        self.assertTrue(ZuulJob('job2', 'gate', {'voting': True}) in jobs)

    def test_copy_as(self):
        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')

        jobs = [job1, job2]

        copy_map.update({
            '/.*/': {
                '/.*/': [{
                    job2.name: {
                        'as': 'job3',
                        'voting': True
                    }
                }]
            }
        })

        copy_jobs(jobs, 'any', 'any')

        self.assertEqual(len(jobs), 3)
        self.assertTrue(ZuulJob('job1', 'check') in jobs)
        self.assertTrue(ZuulJob('job2', 'check') in jobs)
        self.assertTrue(ZuulJob('job3', 'check', {'voting': True}) in jobs)

    def test_copy_by_tag(self):
        tag = 'tag_1'

        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')

        jobs = [job1, job2]

        copy_map.update({
            '/.*/': {
                tag: [{
                    job2.name: {
                        'from': 'check',
                        'to': 'gate',
                        'voting': True
                    }
                }]
            }
        })

        copy_jobs(jobs, 'any', tag)

        self.assertEqual(len(jobs), 3)
        self.assertTrue(ZuulJob('job1', 'check') in jobs)
        self.assertTrue(ZuulJob('job2', 'check') in jobs)
        self.assertTrue(ZuulJob('job2', 'gate', {'voting': True}) in jobs)

    def test_copy_by_tag_and_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')

        jobs = [job1, job2]

        copy_map.update({
            project: {
                tag: [{
                    job2.name: {
                        'from': 'check',
                        'to': 'gate',
                        'voting': True
                    }
                }]
            }
        })

        copy_jobs(jobs, project, tag)

        self.assertEqual(len(jobs), 3)
        self.assertTrue(ZuulJob('job1', 'check') in jobs)
        self.assertTrue(ZuulJob('job2', 'check') in jobs)
        self.assertTrue(ZuulJob('job2', 'gate', {'voting': True}) in jobs)

    def test_copy_skip_unmatched_project(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')

        jobs = [job1, job2]

        copy_map.update({
            project: {
                tag: [{
                    job2.name: {
                        'from': 'check',
                        'to': 'gate',
                        'voting': True
                    }
                }]
            }
        })

        copy_jobs(jobs, 'any', tag)

        self.assertEqual(len(jobs), 2)
        self.assertTrue(ZuulJob('job1', 'check') in jobs)
        self.assertTrue(ZuulJob('job2', 'check') in jobs)
        self.assertTrue(ZuulJob('job2', 'gate', {'voting': True}) not in jobs)

    def test_copy_skip_unmatched_tag(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')

        jobs = [job1, job2]

        copy_map.update({
            project: {
                tag: [{
                    job2.name: {
                        'from': 'check',
                        'to': 'gate',
                        'voting': True
                    }
                }]
            }
        })

        copy_jobs(jobs, project, 'any')

        self.assertEqual(len(jobs), 2)
        self.assertTrue(ZuulJob('job1', 'check') in jobs)
        self.assertTrue(ZuulJob('job2', 'check') in jobs)
        self.assertTrue(ZuulJob('job2', 'gate', {'voting': True}) not in jobs)

    def test_copy_unset_job_option(self):
        tag = 'tag_1'
        project = 'project_1'

        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check', {'voting': True})

        jobs = [job1, job2]

        copy_map.update({
            project: {
                tag: [{
                    job2.name: {
                        'from': 'check',
                        'to': 'gate',
                        'voting': None
                    }
                }]
            }
        })

        copy_jobs(jobs, project, tag)

        self.assertEqual(len(jobs), 3)
        self.assertTrue(ZuulJob('job1', 'check') in jobs)
        self.assertTrue(ZuulJob('job2', 'check', {'voting': True}) in jobs)
        self.assertTrue(ZuulJob('job2', 'gate') in jobs)

    def test_copy_bad_entry(self):
        job1 = ZuulJob('job1', 'check')
        job2 = ZuulJob('job2', 'check')

        jobs = [job1, job2]

        copy_map.update({
            '/.*/': {
                '/.*/': [{
                    job2.name: {
                        'voting': True
                    }
                }]
            }
        })

        self.assertRaises(SystemExit, copy_jobs, jobs, 'any', 'any')
