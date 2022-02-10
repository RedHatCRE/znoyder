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
from distroinfo import info as di


class Distro(object):

    INFO_FILE = 'osp.yml'
    RDOINFO_GIT_URL = 'https://code.engineering.redhat.com/gerrit/ospinfo'

    @staticmethod
    def get_distroinfo():
        return di.DistroInfo(info_files=Distro.INFO_FILE,
                             cache_ttl=24*60*60,  # 1 day in seconds
                             remote_git_info=Distro.RDOINFO_GIT_URL).get_info()
