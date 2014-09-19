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
from config_manager.eucalyptus_properties import EucalyptusProperty
from config_manager.eucalyptus.topology.cluster.blockstorage import BlockStorage
import config_manager.eucalyptus.topology.cluster.blockstorage

from config_manager.eucalyptus.topology.cluster.nodecontroller import NodeController
from config_manager.eucalyptus.topology.cluster.nodecontroller.hyperv import Hyperv
from config_manager.eucalyptus.topology.cluster.nodecontroller.kvm import Kvm
from config_manager.eucalyptus.topology.cluster.nodecontroller.xen import Xen
from config_manager.eucalyptus.topology.cluster.nodecontroller.esxi import Esxi
from config_manager.eucalyptus.topology.cluster.nodecontroller.vsphere import Vsphere

from config_manager.eucalyptus.topology.cluster.blockstorage.ceph import Ceph
from config_manager.eucalyptus.topology.cluster.blockstorage.das import Das
from config_manager.eucalyptus.topology.cluster.blockstorage.emc_vnx import Emc_Vnx
from config_manager.eucalyptus.topology.cluster.blockstorage.emc_vnx_flare31 import Emc_Vnx_Flare31
from config_manager.eucalyptus.topology.cluster.blockstorage.equallogic import Equallogic
from config_manager.eucalyptus.topology.cluster.blockstorage.netapp import Netapp
from config_manager.eucalyptus.topology.cluster.blockstorage.netapp_cluster import Netapp_Cluster
from config_manager.eucalyptus.topology.cluster.blockstorage.overlay import Overlay

from config_manager.eucalyptus.topology.cluster.network.edge_network_config import Edge_Network_Config
from config_manager.eucalyptus.topology.cluster.network.managed_network_config import Managed_Network_Config
from config_manager.eucalyptus.topology.cluster.network.managed_novlan_network_config import Managed_Novlan_Network_Config


_HYPERVISORS = {str(Esxi.__name__).lower(): Esxi,
                str(Hyperv.__name__).lower(): Hyperv,
                str(Kvm.__name__).lower(): Kvm,
                str(Vsphere.__name__).lower(): Vsphere,
                str(Xen.__name__).lower(): Xen}

_BLOCKSTORAGE_TYPES = {str(Ceph.__name__).lower(): Ceph,
                       str(Das.__name__).lower(): Das,
                       str(Emc_Vnx.__name__).lower(): Emc_Vnx,
                       str(Emc_Vnx_Flare31.__name__).lower(): Emc_Vnx_Flare31,
                       str(Equallogic.__name__).lower(): Equallogic,
                       str(Netapp.__name__).lower(): Netapp,
                       str(Netapp_Cluster.__name__).lower(): Netapp_Cluster,
                       str(Overlay.__name__).lower(): Overlay}

_NETWORK_TYPES = modes = {
        'EDGE': Edge_Network_Config,
        'MANAGED': Managed_Network_Config,
        'MANAGED_NOVLAN': Managed_Novlan_Network_Config
    }


class Cluster(BaseConfig):
    def __init__(self,
                 name,
                 hypervisor=None,
                 blockstorage_type=None,
                 description=None,
                 read_file_path=None,
                 write_file_path=None,
                 property_type=None,
                 version=None):
        description = description or "Eucalyptus Cluster Controller Configuration Block"
        self._scheduling_options = ['GREEDY', 'ROUNDROBIN']
        # Create the Eucalyptus software specific properties
        self.eucalyptus_properties.addressespernetwork = EucalyptusProperty(
            name=str(name) + '.cluster.addressespernetwork',
            properties_manager=self.eucalyptus_properties,
            value=None)
        self.eucalyptus_properties.maxnetworkindex = EucalyptusProperty(
            name=str(name) + '.cluster.maxnetworkindex',
            properties_manager=self.eucalyptus_properties,
            value=None)
        self.eucalyptus_properties.maxnetworktag = EucalyptusProperty(
            name=str(name) + '.cluster.maxnetworktag',
            properties_manager=self.eucalyptus_properties,
            value=None)
        self.eucalyptus_properties.minnetworkindex = EucalyptusProperty(
            name=str(name) + '.cluster.minnetworkindex',
            properties_manager=self.eucalyptus_properties,
            value=None)
        self.eucalyptus_properties.minnetworktag = EucalyptusProperty(
            name=str(name) + '.cluster.minnetworktag',
            properties_manager=self.eucalyptus_properties,
            value=None)
        self.eucalyptus_properties.networkmode = EucalyptusProperty(
            name=str(name) + '.cluster.networkmode',
            properties_manager=self.eucalyptus_properties,
            value=None)
        self.eucalyptus_properties.sourcehostname = EucalyptusProperty(
            name=str(name) + '.cluster.sourcehostname',
            properties_manager=self.eucalyptus_properties,
            value=None)
        self.eucalyptus_properties.usenetworktags = EucalyptusProperty(
            name=str(name) + '.cluster.usenetworktags',
            properties_manager=self.eucalyptus_properties,
            value=None)
        self.eucalyptus_properties.vnetnetmask = EucalyptusProperty(
            name=str(name) + '.cluster.vnetnetmask',
            properties_manager=self.eucalyptus_properties,
            value=None)
        self.eucalyptus_properties.vnetsubnet = EucalyptusProperty(
            name=str(name) + '.cluster.vnetsubnet',
            properties_manager=self.eucalyptus_properties,
            value=None)
        self.eucalyptus_properties.vnettype = EucalyptusProperty(
            name=str(name) + '.cluster.vnettype',
            properties_manager=self.eucalyptus_properties,
            value=None)

        self.nc_communication_port = self.create_property(
            json_name='nc_port',
            value = None,
            description="On a NC, this defines the TCP port on which the NC will listen. \n"
                        "On a CC, this defines the TCP port on which the CC will contact NCs."
        )
        self.cc_communication_port = self.create_property(
            json_name='cc_port',
            value=None,
            description=" The TCP port on which the CC will listen"
        )
        self.vm_placemenscheduling_policy = self.create_property(
            json_name='schedule_policy',
            description="""The scheduling policy that the CC uses to choose the NC on which to
                           run each new instance.  Valid settings include GREEDY and ROUNDROBIN.
                           The default scheduling policy is ROUNDROBIN
                        """
        )
        # Create storage and cluster controller configuration (blocks) properties
        self.schedule_policy = self.create_property(json_name='SCHEDPOLICY')
        self.enable_tunneling  = self.create_property(
            json_name='DISABLE_TUNNELING',
            validate_callback=self._validate_reverse_boolean)

        # Store the cluster wide block storage (backend) type, and block storage object
        self.blockstorage_type = self.create_property(
            json_name='blockstorage_type',
            value=blockstorage_type,
            validate_callback=self.validate_blockstorage_type)
        self.block_storage = self.create_property('block_storage', value=None)

        # Store network info in network obj...
        self.network = self.create_property('network', value=None)

        # Store the cluster controller host objects...
        self.cluster_controllers = self.create_property('cluster_controllers', value=[])

        # Store the cluster wide hypervisor type and list of node objects...
        self.nodes = self.create_property('nodes', value=[])
        self.hypervisor_type = self.create_property(
            'hypervisor_type', value=hypervisor, validate_callback=self.validate_hypervisor_type)


        # todo decide if this is needed, or if esx node types are enough/better...
        self.vmware_brokers = self.create_property('vmware_brokers', value=None)

        # Baseconfig init() will read in default values from read_file_path if it is populated.
        super(Cluster, self).__init__(name=name,
                                      description=description,
                                      read_file_path=read_file_path,
                                      write_file_path=write_file_path,
                                      property_type=property_type,
                                      version=version)

    def _validate_reverse_boolean(self, value):
        '''
        Method is intended to make some of the more confusing Eucalyptus properties easier for
        end users to understand by renaming the property and allowing the value(s) to reversed
        where needed to match the  naming.
        Validates the value provided is a boolean or None. Returns the reverse of the boolean,
        or None.
        '''
        #Allow disabling the property with None
        if value is None:
            return None
        assert isinstance(value, bool), \
            'Value must be of type boolean :"{0}"/"{1}"'.format(value, type(value))
        if value:
            return False
        else:
            return True

    def _validate_scheduler(self, value):
        if value is None:
            return None
        value = str(value).upper()
        for valid_value in self._scheduling_options:
            if value == valid_value.upper():
                return value
        valid_str = ", ".join(self._scheduling_options)
        print ('WARNING: Unknown scheduling policy:"{0}". Valid values are:"{1}"'
               .format(value, valid_str))

    def validate_blockstorage_type(self, blockstorage_type):
        try:
            if blockstorage_type is not None:
                _BLOCKSTORAGE_TYPES[str(blockstorage_type).lower()]
        except KeyError:
            hlist = ""
            for key in _BLOCKSTORAGE_TYPES:
                hlist += "{0}, ".format(key)
            raise ValueError('Unknown block storage type:"{0}". Possible types:"{1}"'
                             .format(blockstorage_type, hlist.rstrip(', ')))
        if not hasattr(self, 'blockstorage_type') or not self.blockstorage_type.value:
            return blockstorage_type
        if (blockstorage_type != self.blockstorage_type.value) and self.storage_controllers.value:
            raise ValueError('Must remove storage controllers to change type')
        return blockstorage_type

    def get_available_blockstorage_types(self):
        return _BLOCKSTORAGE_TYPES.keys()

    def add_block_storage(self, block_storage):
        assert isinstance(block_storage, BlockStorage), 'Cant add non block_storage type:{0}' \
            .format(type(block_storage))
        if self.block_storage.value:
            raise ValueError('Delete existing block storage before adding another')
        self.block_storage.value = block_storage

    def create_block_storage(self, name=None, read_file_path=None):
        name = name or self.name.value + "_block_storage"
        if not self.blockstorage_type.value:
            keys = ", ".join(self.get_available_blockstorage_types())
            raise ValueError('Must set cluster blockstorage_type before creating block storage. '
                             'Available types:"{0}"'.format(keys))
        block_storage_class = _BLOCKSTORAGE_TYPES[self.blockstorage_type.value]
        block_storage = block_storage_class(name=name,
                                            cluster_name=self.name.value,
                                            read_file_path=read_file_path)
        self.add_block_storage(block_storage)
        return block_storage

    def delete_block_storage(self):
        self.block_storage.value = None

    def validate_hypervisor_type(self, hypervisor):
        try:
            if hypervisor is not None:
                _HYPERVISORS[str(hypervisor).lower()]
        except KeyError:
            hlist = ""
            for key in _HYPERVISORS:
                hlist += "{0}, ".format(key)
            raise ValueError('Unknown hypervisor type:"{0}". Possible types:"{1}"'
                             .format(hypervisor, hlist.rstrip(', ')))
        if not self.nodes.value:
            return hypervisor
        if hypervisor == self.hypervisor_type.value:
            return hypervisor
        for node in self.nodes.value:
            if node.hypervisor != hypervisor:
                raise ValueError('Must delete all nodes if changing hypervisor type')
        return hypervisor

    def add_nodes(self, nodes):
        if not isinstance(nodes, list):
            nodes = [nodes]
        for node in nodes:
            if not isinstance(node, NodeController):
                raise ValueError('Could not add obj of non-NodeController type:{0}, obj:{1}'
                                 .format(type(node), node))
            if node.hypervisor.value != self.hypervisor_type.value:
                raise ValueError('Node hypervisor type:"{0}" does not match clusters:"{1}"'
                                 .format(node.hypervisor.value, self.hypervisor_type))
            if self.get_node(node.name):
                raise ValueError('Node with name:"{0}" already exists in cluster'.format(node.name))
            self.nodes.value.append(node)

    def get_node(self, name):
        for node in self.nodes.value:
            if node.name.value == name:
                return node
        return None

    def create_node(self, ip, read_file_path=None, write_file_path=None,
                    description=None, version=None):
        if not self.hypervisor_type.value:
            raise ValueError('Must set "hypervisor_type" in cluster before adding nodes')
        node_class = _HYPERVISORS[self.hypervisor_type.value]
        new_node = node_class(hostname=ip,
                              read_file_path=read_file_path,
                              write_file_path=write_file_path,
                              description=description,
                              version=version)
        self.add_nodes(new_node)
        return new_node
