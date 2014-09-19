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

from config_manager.baseconfig import BaseConfig, EucalyptusProperty, EucalyptusProperties
from config_manager.eucalyptus.topology import Topology
import copy
from config_manager.eucalyptus.topology.cluster.nodecontroller import NodeController


class Eucalyptus(BaseConfig):
    def __init__(self, description=None):
        """
        :type self.eucalyptus_properties: EucalyptusProperties
        """
        description = description or "Eucalyptus Cloud Global Configuration Block"

        # Create the Eucalyptus software specific properties
        self.eucalyptus_properties.use_dns_delegation = EucalyptusProperty(
            name='bootstrap.webservices.use_dns_delegation',
            properties_manager=self.eucalyptus_properties, value=None)

        # Create json configuration (blocks) properties
        self.log_level = self.create_property(json_name='log-level')
        self.bind_addr = self.create_property('set_bind_addr')
        self.eucalyptus_repo = self.create_property('eucalyptus-repo')
        self.euca2ools_repo = self.create_property('euca2ools-repo')
        self.enterprise_repo = self.create_property('enterprise-repo')
        self.enterprise = self.create_property('enterprise')
        self.topology = self.create_property('topology')
        self.network = self.create_property('network')
        self.system_properties = self.create_property('system_properties')
        self.install_load_balancer = self.create_property(
            'install-load-balancer', value=True)
        self.install_imaging_worker = self.create_property(
            'install-imaging-worker',
            value=None,
            validate_callback=lambda x: self._validate_is_bool(x) )
        self.cloud_opts = self.create_property(json_name='cloud_opts', value=[])

        super(Eucalyptus, self).__init__(name=None,
                                         description=None,
                                         write_file_path=None,
                                         read_file_path=None,
                                         version=None)

    def _process_json_output(self, json_dict, show_all=False, **kwargs):
        tempdict = copy.copy(json_dict)
        eucaprops = {}
        aggdict = self._aggregate_eucalyptus_properties(show_all=show_all)
        for key in aggdict:
            value = aggdict[key]
            # handle value of 'False' as valid
            if value or value is False:
                eucaprops[key] = aggdict[key]
            elif show_all:
                eucaprops["!" + str(key)] = aggdict[key]
        if eucaprops:
            if 'eucalyptus_properties' not in tempdict:
                tempdict['eucalyptus_properties'] = eucaprops
            else:
                tempdict['eucalyptus_properties'].update(eucaprops)
        return super(Eucalyptus, self)._process_json_output(json_dict=tempdict,
                                                            show_all=show_all,
                                                            **kwargs)

    def add_topology(self, topology):
        self.topology.value = topology

    def create_topology(self, name=None, read_file_path=None):
        topo = Topology(name=name, read_file_path=read_file_path)
        self.add_topology(topo)
        return topo

    def add_enterprise_credentials(self, enterprise):
        self.enterprise.value = enterprise

    def set_bind_addr_value(self, value):
        self.bind_addr.value = value

    def set_log_level(self, log_level):
        self.log_level.value = log_level

    def set_eucalyptus_repo(self, value):
        self.eucalyptus_repo.value = value

    def set_euca2ools_repo(self, value):
        self.euca2ools_repo.value = value

    def set_enterprise_repo(self, value):
        self.enterprise_repo.value = value

    def add_repositories(self, eucalyptus_repo=None, euca2ools_repo=None, enterprise_repo=None):
        if eucalyptus_repo:
            self.set_eucalyptus_repo(eucalyptus_repo)
        if euca2ools_repo:
            self.set_euca2ools_repo(euca2ools_repo)
        if enterprise_repo:
            self.set_enterprise_repo(enterprise_repo)
