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
# The include map allows one to introduce additional jobs to generated results:
# - for every generated template,
# - for a given release tag,
# - for a given project and release tag.
#
# The supported job options are:
# - type: specifiy a pipeline type or types (e.g. 'check', ['check', 'gate'])
# - voting: tell whether it is a voting job (e.g. True, False)
#
additional_jobs = {
  # Format:
  #   'job-name': {options},
  #
  # e.g.
  #   'openstack-docs': {},
}

additional_jobs_by_tag = {
  # Format:
  #   'release-tag': {
  #     'job-name': 'reason',
  #   }
  #
  # e.g.
  #   'osp-17.0': {
  #     'openstack-tox-py39': {'voting': False, 'type': 'gate'},
  #   }
  'osp-17.0': {
    'openstack-tox-py39': {'voting': False, 'type': 'gate'},
  },
}

additional_jobs_by_project_and_tag = {
  # Format:
  #   'project-name': {
  #     'release-tag': {
  #       'job-name': {options},
  #     }
  #   }
  #
  # e.g.
  #   'nova': {
  #     'osp-17.0': {
  #       'openstack-tox-py39': {'voting': False},
  #     },
  #   },
  #
  'gnocchi': {
    'osp-17.0': {
      'openstack-tox-pep8': {'voting': False, 'type': ['check', 'gate']},
    },
  },
}
