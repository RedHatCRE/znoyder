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
from unittest.mock import patch

from znoyder.templater import JOBS_TO_COLLECT_WITH_MAPPING
from znoyder.templater import main


class TestTemplaterMain(TestCase):
    def setUp(self) -> None:
        JOBS_TO_COLLECT_WITH_MAPPING.clear()

    @patch('builtins.print')
    def test_happy_path(self, mock_print):
        JOBS_TO_COLLECT_WITH_MAPPING.update({
            'old1': 'new1',
            'old2': 'new2',
            'old3': 'new3',
        })

        args = Mock()
        args.json = True

        main(args)

        mock_print.assert_called_with(JOBS_TO_COLLECT_WITH_MAPPING)
