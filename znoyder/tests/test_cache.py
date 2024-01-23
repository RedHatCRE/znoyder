#!/usr/bin/env python3
#
# Copyright 2024 Red Hat, Inc.
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
from unittest.mock import mock_open
from unittest.mock import patch

from znoyder.lib.cache import FileCache


def _noop():  # pragma: no cover
    '''Dummy function for counting the calls.'''
    pass


class TestFileCache(TestCase):
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_with_file(self, mock_file, mock_os):
        mock_os.return_value = True
        path = 'some/file/and.extension'

        FileCache(path)

        mock_file.assert_called_once_with(path, 'r')

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_without_file(self, mock_file, mock_os):
        mock_os.return_value = False
        path = 'some/file/and.extension'

        FileCache(path)

        mock_file.assert_not_called()

    @patch('znoyder.tests.test_cache._noop')
    def test_call(self, mock_noop):
        cache = FileCache()

        @cache
        def fibonacci(n: int) -> int:
            '''Helper function to be decorated in tests.'''
            _noop()
            if n < 2:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)

        call1 = fibonacci(10)
        call2 = fibonacci(10)
        call3 = fibonacci(10)

        self.assertEqual(mock_noop.call_count, 11)
        self.assertEqual(len(cache), 11)
        self.assertEqual(call1, call2)
        self.assertEqual(call1, call3)

    @patch('znoyder.tests.test_cache._noop')
    def test_clear(self, mock_noop):
        cache = FileCache()

        @cache
        def fibonacci(n: int) -> int:
            '''Helper function to be decorated in tests.'''
            _noop()
            if n < 2:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)

        fibonacci(10)
        fibonacci(10)
        fibonacci(10)

        self.assertEqual(mock_noop.call_count, 11)
        self.assertEqual(len(cache), 11)

        cache.clear()
        self.assertEqual(len(cache), 0)

        fibonacci(10)
        fibonacci(10)
        fibonacci(10)

        self.assertEqual(mock_noop.call_count, 22)
        self.assertEqual(len(cache), 11)

    def test_mapping(self):
        cache = FileCache()

        self.assertEqual(len(cache), 0)

        cache['aa'] = 1

        self.assertEqual(cache['aa'], 1)
        self.assertEqual(len(cache), 1)

        del cache['aa']

        self.assertEqual(len(cache), 0)
        with self.assertRaises(KeyError):
            cache['aa']

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{aa: 1, bb: 2}')
    def test_reload(self, mock_file, mock_os):
        mock_os.return_value = True
        path = 'some/file/and.extension'

        cache = FileCache(path)

        mock_file.assert_called_once_with(path, 'r')
        self.assertEqual(len(cache), 2)

        cache.clear()

        mock_file.assert_called_once_with(path, 'r')
        self.assertEqual(len(cache), 0)

        cache.reload()

        self.assertEqual(mock_file.call_count, 2)
        self.assertEqual(len(cache), 2)

        self.assertEqual(cache['aa'], 1)
        self.assertEqual(cache['bb'], 2)

    @patch('builtins.open', new_callable=mock_open, read_data='data')
    def test_save(self, mock_file):
        path = 'some/file/and.extension'

        cache = FileCache()
        cache.filename = path
        cache['aa'] = 1
        cache['bb'] = 2
        cache.save()

        expected = '---\naa: 1\nbb: 2\n'

        mock_file.assert_called_once_with(path, 'w')
        mock_write = mock_file.return_value.__enter__().write
        mock_write.assert_any_call(expected)
        mock_write.assert_any_call('\n')
        self.assertEqual(mock_write.call_count, 2)
