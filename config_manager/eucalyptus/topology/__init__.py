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
from config_manager.eucalyptus.topology.cluster import Cluster
from config_manager.eucalyptus.topology.cloud_controller import CloudController
from config_manager.eucalyptus.topology.walrus import Walrus
from config_manager.eucalyptus.topology.ufs import UserFacingServices


class Topology(BaseConfig):
    def __init__(self,
                 name=None,
                 description=None,
                 read_file_path=None,
                 write_file_path=None,
                 version=None):
        description = description or "Eucalyptus Cloud Topology Configuration Block"
        self.cloud_controllers = self.create_property('cloud_controllers', value=[])
        self.object_storage = self.create_property('object_storage')
        self.user_facing_services = self.create_property('user_facing_services')
        self.clusters_property = self.create_property('clusters', value={})
        super(Topology, self).__init__(name=name,
                                       description=description,
                                       write_file_path=write_file_path,
                                       read_file_path=read_file_path,
                                       version=version)

    def _add_clusters(self, clusters):
        if not clusters:
            raise ValueError('add_clusters provided empty value: "{0}"'
                             .format(clusters))
        if not isinstance(clusters, list):
            clusters = [clusters]

        for cluster in clusters:
            assert isinstance(cluster, Cluster), 'add clusters passed non ' \
                                                 'cluster type, cluster:"{0}"' \
                .format(cluster)
            if self.get_cluster(cluster.name.value):
                raise ValueError('Cluster with name:"{0}" already exists'
                                 .format(cluster.name.value))
            self.clusters_property.value[cluster.name.value] = cluster

    def create_cluster(self, name, hypervisor, read_file_path=None, write_file_path=None):
        cluster = Cluster(name=name, hypervisor=hypervisor, read_file_path=read_file_path,
                          write_file_path=write_file_path)
        self._add_clusters(cluster)
        return cluster

    def get_cluster(self, clustername):
        if clustername in self.clusters_property.value:
            return self.clusters_property.value[clustername]
        return None

    def delete_cluster(self, cluster):
        if isinstance(cluster, Cluster):
            cluster = cluster.name.value
        if cluster in self.clusters_property.value:
            self.clusters_property.value.pop(cluster)
        else:
            print 'clustername:"{0}" not in cluster list'.format(cluster)

    def _add_cloud_controllers(self, clcs):
        if clcs is None:
            raise ValueError('add_cloud_controllers provided empty '
                             'value: "{0}"'.format(clcs))
        if not isinstance(clcs, list):
            clcs = [clcs]
        if self.cloud_controllers.value is None:
            self.cloud_controllers = []
        for clc in clcs:
            if not isinstance(clc, CloudController):
                raise ValueError('_add_cloud_controllers requires CloudController type, '
                                 'provided:"{0}"'.format(type(clc)))
            if self.get_cloud_controller(clc.hostname.value):
                raise ValueError('Cloud controller with hostname already exists: "{0}"'
                                 .format(clc.hostname))
            self.cloud_controllers.value.append(clc)

    def create_cloud_controller(self, hostname, default_obj=None,
                                read_file_path=None, write_file_path=None):
        clc = CloudController(hostname=hostname, default_obj=default_obj,
                              read_file_path=read_file_path, write_file_path=write_file_path)
        self._add_cloud_controllers(clc)
        return clc

    def get_cloud_controller(self, hostname):
        if self.cloud_controllers.value:
            for clc in self.cloud_controllers.value:
                if clc.hostname.value == hostname:
                    return clc
        return None

    def delete_cloud_controller(self, hostname):
        clc = self.get_cloud_controller(hostname)
        if clc:
            self.cloud_controllers.value.remove(clc)


    def _add_walrus(self, walrus):
        self.walrus = walrus

    def _add_user_facing_services(self, user_facing_services):
        self.user_facing_services = user_facing_services

    def _aggregate_eucalyptus_properties(self, show_all=False):
        eucaproperties = {}
        for key in self.clusters_property.value:
            cluster = self.clusters_property.value[key]
            eucaproperties.update(cluster._aggregate_eucalyptus_properties(show_all=show_all))
        agg_dict = super(Topology, self)._aggregate_eucalyptus_properties(show_all=show_all)
        eucaproperties.update(agg_dict)
        return eucaproperties
