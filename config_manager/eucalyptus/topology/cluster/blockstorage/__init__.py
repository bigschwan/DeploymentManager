#!/usr/bin/env python

# Copyright 2009-2014 Eucalyptus Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from config_manager.baseconfig import BaseConfig


class BlockStorage(BaseConfig):
    def __init__(self,
                 name=None,
                 description=None,
                 read_file_path=None, 
                 write_file_path=None,
                 property_type=None,
                 version=None,
                 backend_type=None,
                 euca_properties=None,
                 storage_controllers=None,
                 storage_backend=None):
        super(BlockStorage, self).__init__(name=name,
                                           description=None,
                                           read_file_path=None,
                                           write_file_path=None,
                                           property_type=property_type,
                                           version=None)
        self.backend_type = self.create_property(json_name='backend_type',
                                                 value=backend_type)
        self.storage_backends = self.create_property(
            json_name='storage_backend',
            value=storage_backend)
        self.storage_controllers = self.create_property(
            json_name='storage_controllers',
            value=storage_controllers or [])
        self.euca_properties = self.create_property(
            json_name='euca_properties',
            value=euca_properties)
