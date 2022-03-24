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

import logging
import os
from unittest.mock import patch
from unittest import TestCase

from znoyder.cli import process_arguments


logging.disable(logging.CRITICAL)


class TestCli(TestCase):
    """Test cli for znoyder."""

    def shortDescription(self):
        return None

    @patch('argparse.ArgumentParser._print_message')
    def test_browse_empty(self, mock_argpare_print):
        """Test parsing of znoyder browse arguments."""
        cmd = ["browse-osp"]
        # this should fail, since browse-osp requires a command
        self.assertRaises(SystemExit, process_arguments, cmd)

    @patch('argparse.ArgumentParser._print_message')
    def test_browse_components(self, mock_argpare_print):
        """Test parsing of znoyder browse arguments."""
        cmd = "browse-osp components".split()
        args = process_arguments(cmd)
        self.assertEqual(args.command, "components")
        self.assertFalse(args.debug)

    @patch('argparse.ArgumentParser._print_message')
    def test_browse_packages(self, mock_argpare_print):
        """Test parsing of znoyder browse arguments."""
        cmd = ["browse-osp", "packages", "--component",
               "network", "--tag", "osp-17.0", "--output", "osp-patches"]
        args = process_arguments(cmd)
        self.assertEqual(args.command, "packages")
        self.assertFalse(args.debug)
        self.assertEqual(args.component, "network")
        self.assertEqual(args.tag, "osp-17.0")
        self.assertEqual(args.output, "osp-patches")

    @patch('argparse.ArgumentParser._print_message')
    def test_browse_releases(self, mock_argpare_print):
        """Test parsing of znoyder browse arguments."""
        cmd = "browse-osp releases --debug".split()
        args = process_arguments(cmd)
        self.assertEqual(args.command, "releases")
        self.assertTrue(args.debug)

    @patch('argparse.ArgumentParser._print_message')
    def test_download(self, mock_argpare_print):
        """Test parsing of znoyder download arguments."""
        cmd = ["download", "--repo", "repo_url", "--branch",
               "master", "--destination", "dest/"]
        args = process_arguments(cmd)
        self.assertEqual(args.repository, "repo_url")
        self.assertEqual(args.branch, "master")
        self.assertEqual(args.destination, "dest/")
        self.assertTrue(args.errors_fatal)
        self.assertFalse(args.skip_existing)

    @patch('argparse.ArgumentParser._print_message')
    def test_download_missing_destination(self, mock_argpare_print):
        """Test parsing of znoyder download arguments."""
        cmd = ["download", "--repo", "repo_url", "--branch",
               "master"]
        self.assertRaises(SystemExit, process_arguments, cmd)

    @patch('argparse.ArgumentParser._print_message')
    def test_download_missing_repo(self, mock_argpare_print):
        """Test parsing of znoyder download arguments."""
        cmd = ["download", "--destination", "repo_url", "--repo",
               "master"]
        self.assertRaises(SystemExit, process_arguments, cmd)

    @patch('argparse.ArgumentParser._print_message')
    def test_finder(self, mock_argpare_print):
        """Test parsing of znoyder find-jobs arguments."""
        cmd = "find-jobs --dir path --base base --trigger check".split()
        args = process_arguments(cmd)
        verbose = os.environ.get('SHPERER_VERBOSE', False)
        self.assertEqual(args.verbose, verbose)
        self.assertEqual(args.directory, "path")
        self.assertEqual(args.templates, "base")
        self.assertEqual(args.trigger, "check")

    @patch('argparse.ArgumentParser._print_message')
    def test_finder_missing_dir(self, mock_argpare_print):
        """Test parsing of znoyder find-jobs arguments."""
        cmd = "find-jobs --base base --trigger check".split()
        self.assertRaises(SystemExit, process_arguments, cmd)

    @patch('argparse.ArgumentParser._print_message')
    def test_finder_missing_base(self, mock_argpare_print):
        """Test parsing of znoyder find-jobs arguments."""
        cmd = "find-jobs --dir base --trigger check".split()
        self.assertRaises(SystemExit, process_arguments, cmd)

    @patch('argparse.ArgumentParser._print_message')
    def test_finder_missing_trigger(self, mock_argpare_print):
        """Test parsing of znoyder find-jobs arguments."""
        cmd = "find-jobs --dir base --base check".split()
        self.assertRaises(SystemExit, process_arguments, cmd)

    @patch('argparse.ArgumentParser._print_message')
    def test_templates(self, mock_argpare_print):
        """Test parsing of znoyder templates arguments."""
        cmd = "templates --json".split()
        args = process_arguments(cmd)
        self.assertTrue(args.json)

    @patch('argparse.ArgumentParser._print_message')
    def test_generate(self, mock_argpare_print):
        """Test parsing of znoyder generate arguments."""
        cmd = "generate --tag osp-17 --component network --collect-all".split()
        args = process_arguments(cmd)
        self.assertTrue(args.existing)
        self.assertTrue(args.collect_all)
        self.assertFalse(args.download)
        self.assertFalse(args.generate)
        self.assertIsNone(args.name)
        self.assertIsNone(args.aggregate)
        self.assertEqual(args.component, "network")
        self.assertEqual(args.template, "zuul-project")
        self.assertEqual(args.tag, "osp-17")
