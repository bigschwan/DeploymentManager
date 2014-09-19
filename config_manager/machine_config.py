#!/usr/bin/env python
# coding=utf-8

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


class Machine_Config(BaseConfig):
    def __init__(self,
                 hostname,
                 name=None,
                 default_obj=None,
                 description=None,
                 read_file_path=None,
                 write_file_path=None,
                 property_type=None,
                 version=None):
        self.hostname = self.create_property(json_name='hostname',
                                             value=hostname,
                                             description='IP address or FQDN of machine')
        name = name or "Machine: {0}".format(self.hostname.value)
        super(Machine_Config, self).__init__(name=name,
                                             default_obj=default_obj,
                                             description=description,
                                             read_file_path=read_file_path,
                                             write_file_path=write_file_path,
                                             property_type=property_type,
                                             version=version)
