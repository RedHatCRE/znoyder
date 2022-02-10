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
from znoyder.distro import Distro


class Component(object):

    @staticmethod
    def get_components(**kwargs):
        info = Distro.get_distroinfo()
        components = info.get('components')

        if kwargs.get('name'):
            components = [component for component in components
                          if kwargs.get('name') == component.get('name')]

        return components

    @staticmethod
    def exists(component_name: str) -> bool:
        components = [comp['name'] for comp in Component.get_components()]
        return (component_name in components)
