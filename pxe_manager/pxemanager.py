# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2014, Eucalyptus Systems, Inc.
# All rights reserved.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#
# Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the
#   following disclaimer.
#
#   Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other
#   materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Author: Tony Beckham tony@eucalyptus.com
#
import socket
import xmlrpclib
import json

from time import sleep
from paramiko import BadHostKeyException, AuthenticationException, SSHException, SSHClient, AutoAddPolicy


class PxeManager(object):
    def __init__(self, cobbler_url, cobbler_user, cobbler_password, host_manager_client, public_ip_manager_client,
                 private_ip_manager_client, ssh_user="root", ssh_password="foobar"):
        """

        :param cobbler_url: (string) URL of cobbler server
        :param cobbler_user: (string) cobbler user
        :param cobbler_password: (string) cobbler user's password
        :param host_manager_client: (object) ResourceManger object for machines
        :param public_ip_manager_client: (object) ResourceManger object for public IPs
        :param private_ip_manager_client: (object) ResourceManger object for private IPs
        :param ssh_user: (string) user to attempt ssh login to reserved host
        :param ssh_password: (string) password for user of reserved host
        """
        self.cobbler = xmlrpclib.Server(cobbler_url)
        self.token = self.cobbler.login(cobbler_user, cobbler_password)
        self.host_manager = host_manager_client
        self.public_ip_manager = public_ip_manager_client
        self.private_ip_manager = private_ip_manager_client
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.distro = {'esxi51': 'qa-vmwareesxi51u0-x86_64',
                       'esxi50': 'qa-vmwareesxi50u1-x86_64',
                       'centos': 'qa-centos6-x86_64-striped-drives',
                       'rhel': 'qa-rhel6u5-x86_64-striped-drives'}
        self.host_reservation = []
        self.file_name = 'kickstart.check'
        self.public_ip_reservation = []
        self.private_ip_reservation = []

    def make_host_reservation(self, owner, count, job_id, distro):
        """
        Get machines from machine pool
        :param owner: who the reservation is for
        :param count: how many machines to reserve
        :param job_id: unique identifier for the reservation
        :param distro: what OS to install (see the global dict "distro" for valid options)
        :return:
        """
        resources = self.host_manager.find_resources(field="state", value="idle")['_items']
        if len(resources) < count:
            print "Oops...There are not enough free resources to fill your request."
            return

        for i in range(count):
            hostname = resources[i]['hostname']
            data = json.dumps({'hostname': hostname, 'owner': owner, 'state': 'pxe', 'job_id': job_id})
            self.host_manager.update_resource(data)
            self.put_file_on_target(ip=self.cobbler.get_system(hostname)['interfaces']['eth0']['ip_address'],
                                    file_name=self.file_name)
            print "kickstarting host: " + hostname
            self.host_reservation.append(hostname)
            self.kickstart_machine(system_name=hostname, distro=distro)

        '''
        Check that the resources in the reservation are ready
        '''
        print "Waiting 2 minutes for systems to boot"
        sleep(120)
        for resource in self.host_reservation:
            print "Checking status of " + resource
            if not self.is_system_ready(system_name=resource):
                print "Host was not ready within allotted time. Attempting to allocate another machine."
                self.host_reservation.remove(resource)
                self.make_host_reservation(owner=owner, count=1, job_id=job_id, distro=distro)

        print "Request fulfilled."
        return

    def kickstart_machine(self, system_name, distro):
        """
        Kickstart machine with specified OS

        :param system_name:
        :param distro:
        :return:
        """
        system_handle = self.cobbler.get_system_handle(system_name, self.token)
        self.cobbler.modify_system(system_handle, "profile", self.distro[distro], self.token)
        self.cobbler.modify_system(system_handle, "netboot-enabled", 1, self.token)
        self.cobbler.save_system(system_handle, self.token)

        reboot_args = {"power": "reboot", "systems": [system_name]}
        self.cobbler.background_power_system(reboot_args, self.token)
        return

    def is_system_ready(self, system_name):
        """
        Check that a given system can be reached via ssh after it is kickstarted. If it cannot be reached we will
        try another host. Mark the failed attempt in the DB as a "pxe_failed" for later cleanup. On success update the
        DB with the state of the machine. Another check is that we check for the presence of a file that was placed on
        the host prior to kickstart. If this file is present it indicated that kickstart did not happen.

        :param system_name: name of the system to check
        :return:
        """
        sys_ip = self.cobbler.get_system(system_name)['interfaces']['eth0']['ip_address']
        if self.check_ssh(ip=sys_ip):
            if self.check_for_file_on_target(ip=sys_ip, file_name=self.file_name):
                return False
            print "File presence not detected. Kickstart succeeded"
            data = json.dumps({'hostname': system_name, 'state': 'in_use'})
            self.host_manager.update_resource(data)
            return True
        else:
            data = json.dumps({'hostname': system_name, 'owner': '', 'state': 'pxe_failed', 'job_id': ''})
            self.host_manager.update_resource(data)
        return False

    def free_machines(self, field, value):
        """
        free machines that match given criteria by clearing owner and job_id fields

        :param field:
        :param value:
        :return:
        """
        resources = self.host_manager.find_resources(field=field, value=value)['_items']
        for resource in resources:
            system_name = resource['hostname']
            print "Freeing " + system_name
            data = json.dumps({'hostname': system_name, 'owner': '', 'state': 'idle', 'job_id': ''})
            self.host_manager.update_resource(data)
        return

    def put_file_on_target(self, ip, file_name):
        """
        SSH to a host and touch a file there. We can later check for this files existence to determine whether a
        kickstart completed successfully.

        :param ip: (string) IP address of host
        :param file_name: name of file to create
        :return:
        """
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())  # wont require saying 'yes' to new fingerprint
        ssh.connect(ip, username=self.ssh_user, password=self.ssh_password)
        ssh.exec_command('touch ' + file_name)
        ssh.close()
        return

    def check_for_file_on_target(self, ip, file_name):
        """
        SSH to a host and check for the presence of a file.

        :param ip: (string) IP of a host
        :param file_name: Name of file to check if it exists
        :return: True if the file was found
        """
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())  # wont require saying 'yes' to new fingerprint
        ssh.connect(ip, username=self.ssh_user, password=self.ssh_password)
        command = "[ -f /root/" + file_name + " ] && echo OK"
        _, stdout, _ = ssh.exec_command(command)
        if stdout.read():
            ssh.close()
            print "Found a file that should not have been on the host"
            return True
        ssh.close()
        return False

    def check_ssh(self, ip, interval=20, retries=45):
        """
        Attempt to ssh to a given host. Default is to try for 15 minutes

        :param ip: ip of host to try
        :param user: user to log in as
        :param password: user login password
        :param interval: seconds between retries
        :param retries: number of retries
        :return:
        """
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())

        for i in range(retries):
            try:
                print "Attempting ssh to " + ip + "....." + str(i+1) + "/" + str(retries)
                ssh.connect(ip, username=self.ssh_user, password=self.ssh_password)
                print "Obtained ssh connection to " + ip + "!"
                return True
            except (BadHostKeyException, AuthenticationException, SSHException, socket.error) as e:
                print e
                sleep(interval)
        return False

    def get_host_reservation_as_ip(self, reservation):
        """
        Will lookup IP of a given hostname in cobbler server.

        :param reservation: An array of hostnames to get IPs of
        :return: An array of IPs
        """
        reservation_ips = []
        for item in reservation:
            reservation_ips.append(self.cobbler.get_system(item)['interfaces']['eth0']['ip_address'])
        return reservation_ips

    def make_ip_reservation(self, ip_type, job_id, number_of_ips):
        """
        Used to make a reservation of public or private IPs.  Typically the job_id would be the jenkins job or some
        other string that would be unique to the entire reservation. This makes it easier to free the IPs associated
        with the reservation. However, an user's name can also be used*.

        *Use caution when using a user's name when freeing as that would free all for that person. If a user name is
        used for the reservation it is best practice to free those by IP address

        :param ip_type: Type of IP reservation to make (public/private)
        :param job_id: job_id or owner to make the reservation for
        :param number_of_ips: how many IPs to reserve
        :return: an array of the IPs that were reserved
        """
        type_dict = {'public': self.public_ip_manager,
                     'private': self.private_ip_manager}
        reservation_dict = {'public': self.public_ip_reservation,
                            'private': self.private_ip_reservation}
        ip_manager = type_dict[ip_type]
        resources = ip_manager.find_resources(field="owner", value="")['_items']
        if len(resources) < number_of_ips:
            print "Oops...There are not enough free IPs to fill your request."
            return

        for i in range(number_of_ips):
            address = resources[i]['address']
            data = json.dumps({'address': address, 'owner': job_id})
            ip_manager.update_resource(data)
            reservation_dict[ip_type].append(address)
        return reservation_dict[ip_type]

    def free_ip_reservation(self, ip_type, field="owner", value=""):
        """
        Free ip reservation. Usually you would free by owner:job_id to free all for a particular reservation. However,
        it is possible to filter on any field:value. This is useful to free individual IPs

        ex1: to free an entire reservation - field="owner", value="vic-CI-edge-23"

        ex2: to free individual ip - field="address", value="10.111.51.50"

        :param ip_type: Type of IP reservation to free (public/private)
        :param field: Field to filter on (default is owner but can also be address)
        :param value: Criteria to filter on, typically a job_id name
        :return:
        """
        type_dict = {'public': self.public_ip_manager,
                     'private': self.private_ip_manager}
        ip_type = type_dict[ip_type]
        resources = ip_type.find_resources(field=field, value=value)['_items']
        for resource in resources:
            address = resource['address']
            print "Freeing " + address
            data = json.dumps({'address': address, 'owner': ''})
            ip_type.update_resource(data)
        return
