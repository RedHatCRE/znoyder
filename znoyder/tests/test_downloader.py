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
import json
import os
from argparse import Namespace
from dataclasses import dataclass
from unittest import TestCase
from unittest.mock import patch
from tempfile import TemporaryDirectory

from requests.exceptions import RequestException

from znoyder.downloader import (CONTENT_ENDPOINT, GITHUB_API_URL,
                                OPENDEV_API_URL, REPO_ENDPOINT, download_file,
                                download_files_parallel, download_zuul_config,
                                get_raw_url_files_in_repository, main)


@dataclass
class MockHTMLResponse:
    """Mock an HTML response from requests.get."""
    status_code: int
    text: str
    url: str
    content: bytes


class TestDownloader(TestCase):
    """Test the downloader module."""

    def setUp(self):
        self.test_directory = TemporaryDirectory()
        self.dest_dir = self.test_directory.name

    def tearDown(self):
        self.test_directory.cleanup()

    def test_get_raw_url_wrong_repo(self):
        """Test that get_raw_url_files_in_repository fails with unknown url."""
        repo = "repo_url"

        self.assertRaises(SystemExit, get_raw_url_files_in_repository, repo,
                          {}, errors_fatal=True)

    def test_get_raw_url_wrong_repo_errors_non_fatal(self):
        """Test that get_raw_url_files_in_repository fails with unknown url
        and errors_fatal set to False.
        """
        repo = "repo_url"
        data = get_raw_url_files_in_repository(repo, {}, errors_fatal=False)
        self.assertEqual(data, {})

    @patch("requests.get")
    def test_get_raw_url_get_unsuccessful(self, patched_get):
        """Test that get_raw_url_files_in_repository fails when getting
        a response other than 200 and errors_fatal set to True.
        """
        repo = "repo_url.opendev.org"
        endpoint = (OPENDEV_API_URL + REPO_ENDPOINT + CONTENT_ENDPOINT)
        url = endpoint.format(project=repo, path=".", gitref="master")
        patched_get.return_value = MockHTMLResponse(300, '{"errors": ""}',
                                                    url, b"")

        self.assertRaises(SystemExit, get_raw_url_files_in_repository, repo,
                          {}, errors_fatal=True)

    @patch("requests.get")
    def test_get_raw_url_get_unsuccessful_non_fatal(self, patched_get):
        """Test that get_raw_url_files_in_repository fails when getting
        a response other than 200 and errors_fatal set to True.
        """
        repo = "repo_url.opendev.org"
        endpoint = (OPENDEV_API_URL + REPO_ENDPOINT + CONTENT_ENDPOINT)
        url = endpoint.format(project=repo, path=".", gitref="master")
        patched_get.return_value = MockHTMLResponse(300, '{"errors": ""}',
                                                    url, b"")

        data = get_raw_url_files_in_repository(repo, {}, errors_fatal=False)
        self.assertEqual(data, {})
        patched_get.assert_called_with(url=url)

    @patch("requests.get")
    def test_get_raw_url_get_files(self, patched_get):
        """Test that get_raw_url_files_in_repository processes
        correctly a response.
        """
        payload = [{"name": ".github",
                    "path": ".github",
                    "download_url": "url1",
                    "type": "dir"},
                   {
                    "name": ".gitignore",
                    "path": ".gitignore",
                    "download_url": "url2",
                    "type": "file"}]

        repo = "repo_url.opendev.org"
        endpoint = (OPENDEV_API_URL + REPO_ENDPOINT + CONTENT_ENDPOINT)
        url = endpoint.format(project=repo, path=".", gitref="master")
        patched_get.return_value = MockHTMLResponse(200, json.dumps(payload),
                                                    url, b"")
        data = get_raw_url_files_in_repository(repo, {"files": [".github",
                                                                ".gitignore"],
                                                      "directories": []},
                                               errors_fatal=False)
        self.assertEqual(data, {repo: ["url1", "url2"]})

    @patch("requests.get")
    def test_get_raw_url_get_files_github(self, patched_get):
        """Test that get_raw_url_files_in_repository processes
        correctly a response.
        """
        payload = [{"name": ".github",
                    "path": ".github",
                    "download_url": "url1",
                    "type": "dir"},
                   {
                    "name": ".gitignore",
                    "path": ".gitignore",
                    "download_url": "url2",
                    "type": "file"}]

        repo = "repo_url.github.com"
        endpoint = (GITHUB_API_URL + REPO_ENDPOINT + CONTENT_ENDPOINT)
        url = endpoint.format(project=repo, path=".", gitref="master")
        patched_get.return_value = MockHTMLResponse(200, json.dumps(payload),
                                                    url, b"")
        data = get_raw_url_files_in_repository(repo, {"files": [".github",
                                                                ".gitignore"],
                                                      "directories": []},
                                               errors_fatal=False)
        self.assertEqual(data, {repo: ["url1", "url2"]})

    @patch("requests.get")
    def test_get_raw_url_get_directories(self, patched_get):
        """Test that get_raw_url_files_in_repository processes
        correctly a response.
        """
        payload = [{"name": ".github",
                    "path": ".github",
                    "download_url": "url1",
                    "type": "dir"},
                   {
                    "name": ".gitignore",
                    "path": ".gitignore",
                    "download_url": "url2",
                    "type": "file"}]

        repo = "repo_url.opendev.org"
        endpoint = (OPENDEV_API_URL + REPO_ENDPOINT + CONTENT_ENDPOINT)
        url = endpoint.format(project=repo, path=".", gitref="master")
        patched_get.return_value = MockHTMLResponse(200, json.dumps(payload),
                                                    url, b"")
        data = get_raw_url_files_in_repository(repo, {"files": [".gitignore"],
                                                      "directories": [
                                                          ".github"]
                                                      },
                                               errors_fatal=False)
        self.assertEqual(data, {repo: ["url2"],
                                repo+"/.github": ["url2"]})

    @patch("requests.get")
    def test_download_file_exception(self, patched_get):
        """Test that download_file properly  catches any exception occurred
        when sending a request.
        """

        patched_get.side_effect = RequestException
        self.assertRaises(SystemExit, download_file, "", self.dest_dir)

    @patch("requests.get")
    def test_download_file(self, patched_get):
        """Test that download_file properly write the file to download."""

        content = b"Some content\nMore content\n"
        url = "file"
        patched_get.return_value = MockHTMLResponse(200, '{}', "url", content)
        download_file(url, self.dest_dir)
        self.assertTrue(os.path.isdir(self.dest_dir))
        with open(os.path.join(self.dest_dir, url), "rb") as file_obj:
            content_read = file_obj.read()
        self.assertEqual(content, content_read)

    @patch("requests.get")
    def test_download_file_exists(self, patched_get):
        """Test that download_file skips the download if the file already
        exists.
        """
        url = "file"
        content = b"Some content\nMore content\n"
        with open(os.path.join(self.dest_dir, url), "wb") as file_obj:
            file_obj.write(content)

        patched_get.side_effect = RequestException
        download_file(url, self.dest_dir, skip_existing=True)
        # if the call ends without raising, that means that download_file
        # returned early

    @patch("requests.get")
    def test_download_file_parallel(self, patched_get):
        """Test that download_files_parallel properly writes the files
        to download.
        """

        content = b"Some content\nMore content\n"
        urls = ["file1", "file2", "file3"]
        patched_get.return_value = MockHTMLResponse(200, '{}', "url", content)

        download_files_parallel(urls, self.dest_dir)
        self.assertTrue(os.path.isdir(self.dest_dir))
        for url in urls:
            with open(os.path.join(self.dest_dir, url), "rb") as file_obj:
                content_read = file_obj.read()
            self.assertEqual(content, content_read)

    @patch("requests.get")
    def test_download_zuul_config(self, patched_get):
        """Test that download_zuul_config properly writes the files
        to download.
        """
        payload = [{"name": ".zuul.yaml",
                    "path": ".zuul.yaml",
                    "download_url": "url1",
                    "type": "file"},
                   {
                    "name": "zuul.yaml",
                    "path": "zuul.yaml",
                    "download_url": "url2",
                    "type": "file"}]

        content = b"Some content\nMore content\n"
        repo = "repo_url.opendev.org"
        endpoint = (OPENDEV_API_URL + REPO_ENDPOINT + CONTENT_ENDPOINT)
        url = endpoint.format(project=repo, path=".", gitref="master")
        patched_get.return_value = MockHTMLResponse(200, json.dumps(payload),
                                                    url, content)
        out_files = ["url1", "url2"]

        files = download_zuul_config(repository=repo, branch="master",
                                     destination=self.dest_dir)
        self.assertEqual(files, {repo: out_files})
        out_folder = os.path.join(self.dest_dir, repo)
        for name in out_files:
            with open(os.path.join(out_folder, name), "rb") as file_obj:
                content_read = file_obj.read()
            self.assertEqual(content, content_read)

    @patch("requests.get")
    def test_main(self, patched_get):
        """Test that main properly calls the module functions."""
        payload = [{"name": ".zuul.yaml",
                    "path": ".zuul.yaml",
                    "download_url": "url1",
                    "type": "file"},
                   {
                    "name": "zuul.yaml",
                    "path": "zuul.yaml",
                    "download_url": "url2",
                    "type": "file"}]

        content = b"Some content\nMore content\n"
        repo = "repo_url.opendev.org"
        endpoint = (OPENDEV_API_URL + REPO_ENDPOINT + CONTENT_ENDPOINT)
        url = endpoint.format(project=repo, path=".", gitref="master")
        patched_get.return_value = MockHTMLResponse(200, json.dumps(payload),
                                                    url, content)
        out_files = ["url1", "url2"]

        args_mock = Namespace()
        setattr(args_mock, "repository", repo)
        setattr(args_mock, "branch", "master")
        setattr(args_mock, "destination", self.dest_dir)
        main(args_mock)
        out_folder = os.path.join(self.dest_dir, repo)
        for name in out_files:
            with open(os.path.join(out_folder, name), "rb") as file_obj:
                content_read = file_obj.read()
            self.assertEqual(content, content_read)
