#!usr/bin/python
#
# =====================================================================
# Copyright (c) 2012-2013, PLUMgrid, http://plumgrid.com
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
# =====================================================================
#

import sys
import re
import time
import netaddr
from novaclient.v1_1 import client as nova_client
from novaclient import exceptions as nova_exception
from neutronclient.v2_0 import client as neutron_client
from neutronclient.common import exceptions as neutron_exception
from keystoneclient.v2_0 import client as keystone_client
from keystoneclient import exceptions as keystone_exception
from plumgridlib import plumlib
import time

class PGLib():

    def __init__(self, director_server, username, password):
        self.pglib = plumlib.Plumlib(director_server,
                                     "443",
                                     70,
                                     username,
                                     password)

    def add_route(self, tenant_id, router_id, route_name, next_hop, ip_addr, ip_netmask):
        router_db = self._create_router_db(tenant_id, router_id, "router")
        route_op = "ADD"
        route_db = self._create_route_db(route_op, route_name,
                                         ip_addr, ip_netmask, next_hop)
        self.pglib.update_router(router_db, router_id, route_db)

    def delete_route(self, tenant_id, router_id, route_name):
        router_db = self._create_router_db(tenant_id, router_id, "router")
        route_op = "DELETE"
        route_db = self._create_route_db(route_op, route_name,
                                         "", "", "")
        self.pglib.update_router(router_db, router_id, route_db)


    def _create_route_db(self, route_op, route_name, ip_addr,
                         ip_netmask, next_hop):
        route_db = {"route": route_op,
                    "route_name": route_name,
                    "ip_next_hop": next_hop,
                    "ip_address": ip_addr,
                    "ip_address_netmask": ip_netmask}

        return route_db

    def _create_router_db(self, tenant_id, router_id, router_name="rtr_name"):
        router_db = {"status": "ACTIVE",
                          "external_gateway_info": None,
                          "name": router_name,
                          "admin_state_up": True,
                          "tenant_id": tenant_id,
                          "routes": [],
                          "id": router_id}
        return router_db

    def attach_to_tenant(self, tenant_id, router_id, router_ifc_ip, cidr, peer_vd, net_id):
        ipnet = netaddr.IPNetwork(cidr)
        shared_net_db = self._shared_net_db(net_id, tenant_id, peer_vd)
        endpoint = self._endpoint_db("SHARED", net_id)
        link_db = self._link_db(net_id, tenant_id, net_id)
        self.pglib.create_shared_network(shared_net_db)
        port_db = self._create_port_db(tenant_id, net_id, net_id, net_id, router_ifc_ip)
        self.pglib.pgc.create_endpoint(peer_vd, router_id,
                             port_db, ipnet, endpoint)
        self.pglib.link_shared_network(link_db)

    def detach_from_tenant(self, tenant_vd, router_id, peer_vd, net_id):
        shared_net_db = self._shared_net_db(net_id, tenant_vd, peer_vd)
        endpoint = self._endpoint_db("SHARED", net_id)
        link_db = self._link_db(net_id, tenant_vd, net_id)
        self.pglib.unlink_shared_network(link_db)
        self.pglib.pgc.delete_endpoint(peer_vd, router_id,
                                 endpoint)
        self.pglib.delete_shared_network(shared_net_db)

    def _create_port_db(self, tenant_id, port_id, net_id,
                        device_owner_name, ip_addr="10.0.0.4", **kwargs):
        cidr = kwargs.pop('cidr', '10.10.0.0/24')
        gateway_ip = kwargs.pop('gateway_ip', '10.10.0.254')
        pool_start = kwargs.pop('pool_start', '10.10.0.2')
        pool_end = kwargs.pop('pool_end', '10.10.0.253')
        mac = kwargs.pop('mac', 'aa:aa:aa:bb:bb:bb')
        sg_id = kwargs.pop('sg_id', '1234567890')
        port_db = {"status": "ACTIVE",
                        "subnets": [],
                        "name": "network_name",
                        "admin_state_up": True,
                        "tenant_id": tenant_id,
                        "device_owner": device_owner_name,
                        "id": port_id,
                        "shared": False,
                        "name": "",
                        "network_id": net_id,
                        "allocation_pools":
                            [{"start": pool_start, "end": pool_end}],
                        "fixed_ips": [{"ip_address": ip_addr}],
                        "gateway_ip": gateway_ip,
                        "ip_version": 4,
                        "cidr": cidr,
                        "mac_address": mac,
                        "enable_dhcp": True,
                        "security_groups": [sg_id]}
        return port_db

    def _shared_net_db(self, net_id, tenant1, tenant2):
        shared_net_db = {"id": net_id,
                          "vnds": [tenant1, tenant2]}
        return shared_net_db

    def _endpoint_db(self, ep_type, ep_id):
        ep_db = {"endpoint_type": ep_type,
                 "id": ep_id}
        return ep_db

    def _link_db(self, shared_net_id, tenant_id, link_endpoint):
        link_db = {"id": shared_net_id,
                   "tenant_id": tenant_id,
                   "link_endpoint": link_endpoint}

        return link_db

class OSClient():
    """
    OpenStack APIs
    """
    def __init__(self, auth_url, user, tenant, password):
        self.nova_conn = nova_client.Client(user, password, tenant, auth_url,
                                            service_type="compute")

        self.neutron_conn = neutron_client.Client(username=user, password=password,
                                                  tenant_name=tenant, auth_url=auth_url)

        self.key_conn = keystone_client.Client(username=user, password=password,
                                               tenant_name=tenant, auth_url=auth_url)

    def create_tenant(self, tenant_name):
        """
        Creates a new tenant and a user
        @ Input
        tenant_name - Name of the tenant
        @ Output
        Tenant Object
        """
        self.user = const.OS_POD_USERNAME
        self.password = const.OS_POD_PASSWORD
        self.tenant = const.OS_POD_TENANT
        pita_os_role = const.PITA_OS_ROLE
        user_role = self.create_role(pita_os_role)
        new_tenant = self.key_conn.tenants.create(tenant_name)
        tenant_id = [tenant.id for tenant in key.tenants.list() if tenant.name == tenant_name]
        new_user = self.key_conn.users.create(user_name, password, email, tenant_id)
        return new_user

    def create_vm(self, name, net_list, image_name, flavor_name, config_drive=False, files=None, userdata=None, meta=None):
        """Creates a VM in the Openstack setup

        Args:
            name: name of the VM
            netid: Network ID to connect to
        """
        nics = []
        for net_db in net_list:
            nics.append({"net-id": net_db["net"], "v4-fixed-ip": net_db["ip"]})

        image = self.get_os_image(image_name)
        flavor = self.get_os_flavor(flavor_name)

        vm = self.nova_conn.servers.create("%s" % name, image, flavor,
                                           nics=nics, config_drive=config_drive, files=files, userdata=userdata,meta=meta)


        return vm

    def delete_vm(self, vm):
        """
        Deletes an instance from openstack setup
        @Input
        vm - Openstack VM Object to be deleted
        """
        self.user = const.OS_POD_USERNAME
        self.password = const.OS_POD_PASSWORD
        self.tenant = const.OS_POD_TENANT
        try:
            self.nova_conn.servers.delete(vm.handle)
        except:
            raise Exception("Deletion of virtual machine %s failed", vm.name)

    def reboot_vm(self, vmhan):
        """
        Reboots a VM in the Openstack setup
        @Input
        vm - object of the VM to reboot
        """
        self.nova_conn.servers.reboot(vmhan)

    def create_network(self, name, external_net=False, net_type=None, phy_net=None, vlan=None, tenant_id=None):
        request_body = {"network": {"name": "%s" % name}}
        if external_net:
            request_body["network"]["router:external"] = True
        if net_type:
            request_body["network"]["provider:physical_network"] = phy_net
            request_body["network"]["provider:network_type"] = net_type
            if net_type == "vlan":
                request_body["network"]["provider:segmentation_id"] = vlan
        if tenant_id:
            request_body["network"]["tenant_id"] = tenant_id
        net = self.neutron_conn.create_network(request_body)
        return net

    def create_subnet(self, network_id, cidr, pool_start, pool_end, gateway, dhcp_enable):
        request_body = {"subnet": {"network_id": "%s" %
                                       network_id, "ip_version": 4,
                                       "cidr": "%s" % cidr,
                                       "allocation_pools": [{"start":
                                       "%s" % pool_start, "end": "%s"
                                       % pool_end}]}}
        if not dhcp_enable:
            request_body["subnet"]["enable_dhcp"] = "false"

        if gateway:
            request_body["subnet"]["gateway_ip"] = gateway

        sub = self.neutron_conn.create_subnet(request_body)
        return sub

    def create_port(self, ipaddr, net_id, subnet_id, **kwargs):
        net_name = self.get_net_by_id(net_id)["network"]["name"]
        port = self.neutron_conn.create_port(
            {"port": {"network_id": net_id,
                      "device_owner": "compute:nova",
                      "fixed_ips": [{"ip_address": ipaddr,
                                     "subnet_id": subnet_id}]}})
        return port

    def get_port(self, vm, **kwargs):
        list_ports = self.neutron_conn.list_ports()
        for port in list_ports["ports"]:
            if port["device_id"] == vm.vm_id:
                for req_dict in port["fixed_ips"]:
                    if req_dict["ip_address"] == vm.get_ip_addr():
                        return port

    def get_list_ports(self, **kwargs):
        list_ports = self.neutron_conn.list_ports()
        return list_ports

    def delete_port(self, port, **kwargs):
        self.neutron_conn.delete_port(port["id"])

    def create_router(self, router_name, **kwargs):
        router = self.neutron_conn.create_router({"router": {"name": "%s" % router_name}})
        return router

    def add_interface_router(self, router_id, subnet_id, **kwargs):
        ifc = self.neutron_conn.add_interface_router(router_id,
                                                     {"subnet_id": "%s" % subnet_id})
        return ifc

    def remove_interface_router(self, router, subnet_id, **kwargs):
        self.neutron_conn.remove_interface_router(router.router_id, {"subnet_id": "%s" % subnet_id})

    def update_router(self, router, ext_network_id, **kwargs):
        updated_router = self.neutron_conn.update_router(router.router_id,
                                                         {"router":
                                                         {"external_gateway_info":
                                                         {"network_id": "%s" % Ext_Network_ID}}})
        return updated_router

    def remove_gateway_router(self, router_id, **kwargs):
        updated_router = self.neutron_conn.remove_gateway_router(router_id)
        return updated_router

    def create_floating_ip(self, ext_net_ID, port_id, ipaddr, **kwargs):
        floating_ip = self.neutron_conn.create_floatingip({"floatingip": {"floating_network_id": "%s" % ext_net_ID}})

        floating_ip_id = floating_ip["floatingip"]["id"]
        floating_ip_dict = {"floatingip": {"port_id": "%s" % port_id,
                                           "fixed_ip_address": "%s" % ipaddr}}
        floating_ip_updated = self.neutron_conn.update_floatingip(floating_ip_id, floating_ip_dict)
        return floating_ip_updated

    def delete_floating_ip(self, floating_ip, **kwargs):
        floating_ip_id = floating_ip["floatingip"]["id"]
        self.neutron_conn.delete_floatingip(floating_ip_id)

    def get_vm_by_id(self, id_vm):
        return self.nova_conn.servers.get(id_vm)

    def shutdown(self):
        """
        remove all the instance, network, subnet and router that were
        created in the openstack controller
        """
        if not self.nosetup:
            super(OSController, self).shutdown()

        self.user = const.OS_POD_USERNAME
        self.password = const.OS_POD_PASSWORD
        self.tenant = const.OS_POD_TENANT
        pita_os_role = const.PITA_OS_ROLE
        for tenant in self.key_conn.tenants.list():
            user_list = tenant.list_users()
            for user in user_list:
                roles = self.key_conn.roles.roles_for_user(user.id, tenant.id)
                for role in roles:
                    if role.name == pita_os_role:
                        self.key_conn.users.delete(user.id)
                        self.key_conn.tenants.delete(tenant.id)

        # delete all network and workload VM
        for vm in self.nova_conn.servers.list(search_opts={"all_tenants": 1}):
            try:
                vm.delete()
            except:
                pass

        self.list_port = self.neutron_conn.list_ports()['ports']
        for port in self.list_port:
            try:
                self.neutron_conn.delete_port(port['id'])
            except:
                pass

        self.list_router = self.neutron_conn.list_routers()['routers']
        for router in self.list_router:
            try:
                self.neutron_conn.delete_router(router['id'])
            except:
                pass

        self.list_subnet = self.neutron_conn.list_subnets()['subnets']
        for subnet in self.list_subnet:
            try:
                self.neutron_conn.delete_subnet(subnet['id'])
            except:
                pass

        self.list_network = self.neutron_conn.list_networks()['networks']
        for network in self.list_network:
            try:
                self.neutron_conn.delete_network(network['id'])
            except:
                pass

    def get_os_image(self, image_name):
        """
        Check if an image exists in OpenStack
        @Input
        image_name -- Name of the OpenStack image
        """
        try:
            image = self.nova_conn.images.find(name=image_name)
            return image
        except nova_exception.NotFound:
            err_msg = ('OpenStack image: %s needs to be uploaded'
                       ' before proceeding') % image_name
            raise Exception(err_msg)

    def get_os_flavor(self, flavor_name):
        """
        Check if an flavor exists in OpenStack
        @Input
        flavor_name -- Name of the OpenStack Nova flavor
        """
        try:
            flavor = self.nova_conn.flavors.find(name=flavor_name)
            return flavor
        except nova_exception.NotFound:
            err_msg = ('OpenStack flavor: %s needs to be created'
                       ' before proceeding') % flavor_name
            raise Exception(err_msg)

    def flavor_list(self):
         return self.nova_conn.flavors.list()

    def image_list(self):
        return self.nova_conn.images.list()

    def create_flavor(self, name, ram=512, vcpus=1, disks=1):
        """
        Create custom flavor for OpenStack test cases
        @Input
        name -- Flavor name
        ram -- RAM size in MBs
        vcpus -- Number of vcpus
        disk -- Disk size in GBs
        """
        self.nova_conn.flavors.create(name, ram, vcpus, disks)

    def create_role(self, role_name):
        """
        Create a role for OpenStack user
        @Input
        role_name -- Name of the role
        """
        try:
            role = self.key_conn.roles.create(role_name)
            return role
        except keystone_exception.Conflict:
            return self.get_role(role_name)
        except Exception:
            raise

    def get_role(self, role_name):
        """
        Gets the role object for a given OpenStack role
        @Input
        role_name -- Name of the role
        """
        roles = self.key_conn.roles.list()
        for role in roles:
            if role.name == role_name:
                return role
        return None

    def create_security_group(self, name, description, **kwargs):
        """
        Creates a security group with default security group rules
        @Input
        name - name of the security group
        description - description for security group
        @Returns
        JSON response for create_security_group in Neutron
        """
        tenant_name = kwags["tenant"]
        request_body = {"security_group": {"name": "%s" % name,
                                           "description": "%s" % description}}
        sec_group = self.neutron_conn.create_security_group(request_body)
        return sec_group

    def list_security_groups(self, **kwargs):
        list_sec_groups = self.neutron_conn.list_security_groups()
        return list_sec_groups

    def create_security_group_rule(self, sec_group, **kwargs):
        direction = kwargs.pop("direction", "ingress")
        protocol = kwargs.pop("protocol", "")
        port_min = kwargs.pop("port_min", "")
        port_max = kwargs.pop("port_max", "")
        remote_ip = kwargs.pop("remote_ip", "")
        remote_sec_gp = kwargs.pop("remote_group", "")
        request_body = {"security_group_rule": {"direction": "%s" % direction,
                                                "ethertype": "IPv4",
                                                "security_group_id": "%s" % sec_group.group_id}}

        if protocol:
            request_body["security_group_rule"]["protocol"] = protocol
        if port_min and port_max:
            request_body["security_group_rule"]["port_range_min"] = port_min
            request_body["security_group_rule"]["port_range_max"] = port_max
        if remote_ip:
            request_body["security_group_rule"]["remote_ip_prefix"] = remote_ip
        if remote_sec_gp:
            request_body["security_group_rule"]["remote_group_id"] = remote_sec_gp.group_id

        sec_rule = self.neutron_conn.create_security_group_rule(request_body)
        return sec_rule

    def list_security_group_rules(self, **kwargs):
        """
        Lists of all security group rules a specific tenant can access
        @Returns
        JSON response for list_security_groups_rules in Neutron
        """
        list_sec_rules = self.neutron_conn.list_security_group_rules()
        return list_sec_rules

    def delete_security_group_rule(self, sec_rule_id, **kwargs):
        self.neutron_conn.delete_security_group_rule(sec_rule_id)

    def get_net_by_id(self, net_id):
        return self.neutron_conn.show_network(net_id)

    def get_tenant_id(self, tenant_name):
        tenant_id = [ten.id for ten in self.key_conn.tenants.list() if ten.name == tenant_name]
        return tenant_id[0]

    def delete_default_sg(self, sg_id):
        self.neutron_conn.delete_security_group(sg_id)
        #FIXME(fawadk) Seen another race condition
        time.sleep(12)

    def get_default_sg_id(self):
        sgs = self.list_security_groups()
        for sg in sgs["security_groups"]:
            if sg["name"] == "default":
                return sg["id"]
        return None
