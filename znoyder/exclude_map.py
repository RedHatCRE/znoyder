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
# The exclude maps allows you to filter out some jobs from generated results
# by matching them on different attributes:
# - all jobs with a specific name (for all projects/tags, use with caution!),
# - jobs with specific name for a given release tag,
# - jobs with a specific name for a given project and release tag.
#

excluded_jobs = {
  # Format:
  #   'job-name': 'reason',
  #
  # e.g.
  #   'openstack-docs': 'code is the best and only documentation one needs',
}

excluded_jobs_by_tag = {
  # Format:
  #   'release-tag': {
  #     'job-name': 'reason',
  #   }
  #
  # e.g.
  #   'osp-17.0': {
  #     'openstack-tox-py37': 'not available in repos',
  #   }
  'osp-17.0': {
    'openstack-tox-py36': 'OSP 17 release is not using py38 and lower',
    'openstack-tox-py37': 'OSP 17 release is not using py38 and lower',
    'openstack-tox-py38': 'OSP 17 release is not using py38 and lower',
  },
}

excluded_jobs_by_project_and_tag = {
  # Format:
  #   'project-name': {
  #     'release-tag': {
  #       'job-name': 'reason',
  #     }
  #   }
  #
  # e.g.
  #  'nova': {
  #     'osp-17.0': {
  #        'openstack-tox-py36': 'we do not support this Python version',
  #        'openstack-tox-py38': 'we do not support this Python version',
  #     },
  #  },
  #
  'nova': {
     'osp-17.0': {
        'openstack-tox-py36': 'we do not support this Python version',
        'openstack-tox-py38': 'we do not support this Python version',
     },
  },
}
