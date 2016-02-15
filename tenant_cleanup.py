#!/usr/bin/env python
# Copyright (c) 2014, PLUMgrid, http://plumgrid.com
#
# This source is subject to the PLUMgrid License.
# All rights reserved.
#
# THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF
# ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
# PARTICULAR PURPOSE.
#
# PLUMgrid confidential information, delete if you are not the
# intended recipient.
#

import os
import sys
from optparse import OptionParser
import traceback
import time
#FER from plumgridlib.common import pg_common


from keystoneclient.v2_0 import client as keystone_client
from novaclient.v1_1 import client as nova_client
from neutronclient.v2_0 import client as neutron_client

class OpenStackCleanup(object):
    """
    Openstack cleanup script. Cleans the VMs, ports, networks, subnets on the all the tenants
    tc = OpenStackCleanup(options.nos, options.user, options.password, options.tenant, options.debug)
    tc.open_stack_cleanup()

    @Input
    user -- user to login to Openstack
    password --- password for authentication
    tenant ----  tenant name
    authurl ---- authentication URL for keystone
    debug ---- Enabling debugging
    """
    def __init__(self, user, password, tenant, authurl, director_plumgrid,
                                       director_port,
                                       timeout,
                                       director_admin,
                                       director_password, debug):
        """
         Validates input
         connects to rest interface using HTTP
        """
        if debug:
            print "init"
        self.user = user
        self.password = password
        self.tenant = tenant
        self.debug = True
        self.authurl = authurl

        #FER self.pgc = pg_common.CommonLib(director_plumgrid,
        #                              director_port,
        #                              timeout,
        #                              director_admin,
        #                              director_password)

        if self.debug:
            print "user info: %s" % self.user
            print "password info: %s" % self.password
            print "tenant info: %s" % self.tenant
            print "auth url : %s" % self.authurl


    def open_stack_cleanup(self, tenant, tenant_id):
        """
        Open stack cleanup
        """
      #FER  self.pgc._delete_vnd(tenant_id)
        self.nova_cleanup(tenant)
        self.neutron_cleanup(tenant)


    def nova_cleanup(self, tenant):
        print "Cleaning up Nova for tenant %s" % tenant
        """
        Nova Cleanup
        @Input
        tenant -- tenant name
        """
        if self.debug:
            print "cleaning nova for tenant %s" % tenant
        try:
            self.nova = nova_client.Client("%s" % tenant, "%s" % self.password, "%s" % tenant, auth_url="%s" % self.authurl, service_type="compute")
            self.vminstances = [vm.name for vm in self.nova.servers.list()]
            if self.debug:
                print "vm list %s" % self.vminstances
            for vm in self.nova.servers.list():
                if self.debug:
                    print "delete vm %s" % vm.name
                vm.delete()
            if self.nova.servers.list():
                # This sleep to make VM is deleted properly before delete port
                # is called.
                time.sleep(12)
        except:
            pass

    def neutron_cleanup(self, tenant):
        print "Cleaning up Neutron for tenant %s" % tenant
        """
        Quantum cleanup script
        @Input
        tenant -- tenant name
        """
        if self.debug:
            print "cleaning neutron for tenant %s" % tenant
        try:
            self.neutron = neutron_client.Client(username="%s" % tenant, password="%s" % self.password, tenant_name="%s" % tenant, auth_url="%s" % self.authurl)
        except:
            pass
        else:
            if self.debug:
                print "network list %s" % self.neutron.list_networks()
                print "subnet list %s" % self.neutron.list_subnets()
                print "port list %s" % self.neutron.list_ports()

            self.list_port = self.neutron.list_ports()['ports']
            for port in self.list_port:
                if self.debug:
                    print "delete port %s %s" % (port['id'], port['name'])
                self.neutron.delete_port(port['id'])

            self.list_router = self.neutron.list_routers()['routers']
            for router in self.list_router:
                if self.debug:
                    print "delete router %s %s" % (router['id'], router['name'])
                self.neutron.delete_router(router['id'])
            self.list_subnet = self.neutron.list_subnets()['subnets']

            for subnet in self.list_subnet:
                if self.debug:
                    print "delete subnet %s %s" % (subnet['id'], subnet['name'])
                self.neutron.delete_subnet(subnet['id'])
            self.list_network = self.neutron.list_networks()['networks']

            for network in self.list_network:
                if not network["router:external"]:
                    self.neutron.delete_network(network['id'])
                    if self.debug:
                        print "delete network %s %s" % (network['id'], network['name'])
