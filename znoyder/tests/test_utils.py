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

from znoyder.utils import drop_nones_from_dict
from znoyder.utils import match
from znoyder.utils import merge_dicts
from znoyder.utils import sort_dict_by_keys


class TestDropper(TestCase):
    def test_drop_nones_from_dict(self):
        actual = drop_nones_from_dict({'a': 1, 'b': 2, 'c': None})
        expected = {'a': 1, 'b': 2}
        self.assertEqual(actual, expected)

        actual = drop_nones_from_dict({'a': 1, 'b': {'c': 2, 'd': None}})
        expected = {'a': 1, 'b': {'c': 2}}
        self.assertEqual(actual, expected)


class TestMatcher(TestCase):
    def test_match(self):
        self.assertTrue(match('foobar', 'foobar'))
        self.assertFalse(match('foobar', 'foo'))
        self.assertTrue(match('foobar', '/foo/'))


class TestMerger(TestCase):
    def test_merge_dicts(self):
        actual = merge_dicts({'a': 1, 'b': 2}, {'b': 2})
        expected = {'a': 1, 'b': 2}
        self.assertEqual(actual, expected)

        actual = merge_dicts({'a': 1, 'b': {'c': 2}}, {'b': {'d': 3}})
        expected = {'a': 1, 'b': {'c': 2, 'd': 3}}
        self.assertEqual(actual, expected)

        self.assertRaises(Exception, merge_dicts,
                          {'a': 1, 'b': {'c': 2}}, {'b': {'c': 3}})


class TestSorter(TestCase):
    def test_sort_dict_by_keys(self):
        actual = sort_dict_by_keys({'b': 1, 'a': 4, 'c': 3})
        expected = {'a': 4, 'b': 1, 'c': 3}
        self.assertEqual(actual, expected)

        actual = sort_dict_by_keys({'b': {'g': 6, 'e': 7, 'f': 5}, 'a': 4})
        expected = {'a': 4, 'b': {'e': 7, 'f': 5, 'g': 6}}
        self.assertEqual(actual, expected)
