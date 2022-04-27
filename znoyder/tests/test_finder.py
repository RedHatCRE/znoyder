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
import os
from argparse import Namespace
import logging
from unittest import TestCase
from unittest.mock import patch, call
from tempfile import TemporaryDirectory

from znoyder.finder import find_jobs
from znoyder.finder import find_triggers
from znoyder.finder import find_templates
from znoyder.finder import main
from znoyder.lib.exceptions import TriggerTypeError
from znoyder.lib.exceptions import PathError
from znoyder.lib.zuul import JobTriggerType


logging.disable(logging.CRITICAL)


EXAMPLE_ZUUL_CONFIG = """
- project:
    templates:
      - template1
      - template2
    check:
      jobs:
        - job1
        - job2

- project-template:
    template1:
    name: template1
    check:
      jobs:
        - job1
        - job2
- project-template:
    template2:
    name: template2
    check:
      jobs:
        - job1
        - job2

"""


class TestFinder(TestCase):
    """Test the downloader module."""

    def shortDescription(self):  # pragma: no cover
        return None

    def setUp(self):
        self.test_directory = TemporaryDirectory()
        self.dest_dir = self.test_directory.name
        self.file_name = os.path.join(self.dest_dir, "zuul.d")
        with open(self.file_name, "w", encoding="utf-8") as file_write:
            file_write.write(EXAMPLE_ZUUL_CONFIG)

    def tearDown(self):
        self.test_directory.cleanup()

    def test_find_triggers(self):
        """Tests that find_triggers works correctly."""
        triggers = "experimental,post,gate,check,templates"
        result = find_triggers(triggers)
        expected = [JobTriggerType.EXPERIMENTAL, JobTriggerType.POST,
                    JobTriggerType.GATE, JobTriggerType.CHECK,
                    JobTriggerType.TEMPLATES]
        self.assertEqual(result, expected)

    def test_find_triggers_nonexisting_trigger(self):
        """Test that find_triggers fails with unknown trigger."""
        trigger = "unknown"

        self.assertRaises(TriggerTypeError, find_triggers, trigger)

    def test_find_jobs(self):
        """Test find_jobs."""

        output = find_jobs(self.dest_dir, [], [JobTriggerType.CHECK])
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0].job_name, "job1")
        self.assertEqual(output[0].job_trigger_type, "check")
        self.assertEqual(output[1].job_name, "job2")
        self.assertEqual(output[1].job_trigger_type, "check")

    def test_find_templates(self):
        """Test find_teamplates."""
        output = find_templates(self.dest_dir, [JobTriggerType.CHECK])
        self.assertEqual(len(output), 2)
        template1, template2 = output
        self.assertEqual(template1.template_name, "template1")
        self.assertEqual(template1.template_jobs[0].job_name, "job1")
        self.assertEqual(template1.template_jobs[1].job_name, "job2")
        self.assertEqual(template1.template_jobs[0].job_trigger_type, "check")
        self.assertEqual(template1.template_jobs[1].job_trigger_type, "check")
        self.assertEqual(template2.template_name, "template2")
        self.assertEqual(template2.template_jobs[0].job_name, "job1")
        self.assertEqual(template2.template_jobs[1].job_name, "job2")
        self.assertEqual(template2.template_jobs[0].job_trigger_type, "check")
        self.assertEqual(template2.template_jobs[1].job_trigger_type, "check")

    @patch('builtins.print')
    def test_main(self, mock_print):
        """Test that main properly calls the module functions."""
        args_mock = Namespace()
        setattr(args_mock, "directory", self.dest_dir)
        setattr(args_mock, "verbose", True)
        setattr(args_mock, "templates", self.dest_dir)
        setattr(args_mock, "trigger", "check")
        main(args_mock)
        calls = [call("check: job1"), call("check: job2"),
                 call("check: job1 in template template1"),
                 call("check: job2 in template template1"),
                 call("check: job1 in template template2"),
                 call("check: job2 in template template2")]
        mock_print.assert_has_calls(calls)
        self.assertEqual(mock_print.call_count, 6)

    @patch('znoyder.finder._cli_find_jobs')
    def test_main_raises(self, mock_func):
        """Test that main properly calls the module functions."""
        args_mock = Namespace()
        setattr(args_mock, "directory", self.dest_dir)
        setattr(args_mock, "verbose", True)
        setattr(args_mock, "templates", self.dest_dir)
        setattr(args_mock, "trigger", "check")
        mock_func.side_effect = PathError("Error body")
        self.assertRaises(SystemExit, main, args_mock)
