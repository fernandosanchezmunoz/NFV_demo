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

import argparse
import subprocess
import ipaddr
import pg_scripts_helper as api_helper
import os_client
import sys
import time

"""
 This script will deploy Tenant VD as shown below.
"""

topology = ("+--------------------------------------------------------------------------+\n"
            "|                                                                          |\n"
            "|   TO+INTERNET                                                            |\n"
            "|   +-+--+-----+                                                           |\n"
            "|        |                                                                 |\n"
            "|   +----+------+                                                          |\n"
            "|   |   Port    |                                                          |\n"
            "|   | Connector |                                                          |\n"
            "|   +-+------+--+                                                          |\n"
            "|        |                                                                 |\n"
            "|   +----+---+--+                                                          |\n"
            "|   | NETWORK|A |                                                          |\n"
            "|   +-+------+--+                                                          |\n"
            "|     |                                                                    |\n"
            "|  +--+----+  +--+----+     +-----+-+----+                                 |\n"
            "|  |  VM1-2|--|  VM3  |---- + NETWORK|B  +                                 |\n"
            "|  +----+--+  +-------+     +-----+-+----+                                 |\n"
            "|       |     |                                                            |\n"
            "|   +---+----++-+--------------------------------------------------+       |\n"
            "|   |                           NETWORK|D                          |       |\n"
            "|   +--------------------------------------------------------------+       |\n"
            "|      |       |         |        |        |        |       |      |       |\n"
            "|  +-----+   +-----+  +-----+  +-----+  +-----+  +-----+  +-----+  +-----+ |\n"
            "|  | VM2 |   | VM2 |  | VM2 |  | VM2 |  | VM2 |  | VM2 |  | VM2 |  | VM2 | |\n"
            "|  +-----+   +-----+  +-----+  +-----+  +-----+  +-----+  +-----+  +-----+ |\n"
            "|      |       |         |        |        |        |       |      |       |\n"
            "|   +---+----++-+--------------------------------------------------+       |\n"
            "|   |                           NETWORK|C                          |       |\n"
            "|   +--+-----------------------------------------------------------+       |\n"
            "|      |                                                                   |\n"
            "|   +----+                                                                 |\n"
            "|   |VM14|                                                                 |\n"
            "|   +-+--+                                                                 |\n"
            "|     |                                                                    |\n"
            "|   +----+---+--+                                                          |\n"
            "|   | NETWORK|A |                                                          |\n"
            "|   +-+------+--+                                                          |\n"
            "|                                                           |              |\n"
            "|   +----+---+--+                                                          |\n"
            "|   |  PORT     |                                                          |\n"
            "|   | CONNECTOR |                                                          |\n"
            "|   +-+------+--+                                                          |\n"
            "|      |                                                                   |\n"
            "|   +-------------+                                                        |\n"
            "|    TO+MPLS+CORE                                                          |\n"
            "|                                                                          |\n"
            "+--------------------------------------------------------------------------+\n")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create Tenant Virtual Domain')

    # Authentication parameters

    parser.add_argument('--config_file', required=True,
                    help='Configuration file for the script', default=None)

    parser.add_argument('--os_auth_url', required=False,
                    help='OpenStack Authentication URL. For example: http://10.0.3.4:5000/v2.0/',
                    default=None)

    parser.add_argument('--os_tenant_username', required=False,
                    help='Username', default=None)

    parser.add_argument('--os_tenant_password', required=False,
                    help='Username', default=None)

    parser.add_argument('--os_tenant_name', required=False,
                    help='Name of the tenant', default=None)

    parser.add_argument('--os_admin_user', required=False,
                    help='Username', default=None)

    parser.add_argument('--os_admin_password', required=False,
                    help='Username', default=None)

    parser.add_argument('--os_admin_tenant', required=False,
                    help='Name of the tenant', default=None)

    parser.add_argument('--pg_director_ip', required=False,
                        help='PLUMgrid Director IP',
                        default=None)

    parser.add_argument('--pg_username', required=False,
                        help='Username', default=None)

    parser.add_argument('--pg_password', required=False,
                        help='Username', default=None)

    args = parser.parse_args()
    CONF = args.config_file
    existing_conf = api_helper.get_config_section(CONF, "Creds")
    check_conf = api_helper.check_config_section(CONF, "topology")
    if check_conf and check_conf["type"] == "nfv":
        print "NFV VD"
    else:
        print "Configuration not found for NFV VD"
        sys.exit(1)


    AUTH_URL = api_helper.get_config_item("os_auth_url", existing_conf, args.os_auth_url)
    USERNAME = api_helper.get_config_item("os_tenant_username", existing_conf, args.os_tenant_username)
    TENANT = api_helper.get_config_item("os_tenant_name", existing_conf, args.os_tenant_name)
    PASSWORD = api_helper.get_config_item("os_tenant_password", existing_conf, args.os_tenant_password)
    ADMIN_USER = api_helper.get_config_item("os_admin_user", existing_conf, args.os_admin_user)
    ADMIN_TENANT = api_helper.get_config_item("os_admin_tenant", existing_conf, args.os_admin_tenant)
    ADMIN_PASSWORD = api_helper.get_config_item("os_admin_password", existing_conf, args.os_admin_password)
    PG_IP = api_helper.get_config_item("pg_director_ip", existing_conf, args.pg_director_ip)
    PG_USER = api_helper.get_config_item("pg_username", existing_conf, args.pg_username)
    PG_PASSWORD = api_helper.get_config_item("pg_password", existing_conf, args.pg_password)

    print ("This script is going to deploy the following topology."
           "Please enter all the configurations correctly\n")
    print topology


    tenant_handle = os_client.OSClient(AUTH_URL, USERNAME, TENANT, PASSWORD)
    admin_handle = os_client.OSClient(AUTH_URL, ADMIN_USER, ADMIN_TENANT, ADMIN_PASSWORD)

#FER    sg_id = tenant_handle.get_default_sg_id()
#FER    admin_handle.delete_default_sg(sg_id)
    tenant_handle.get_default_sg_id()

    tenant_id = admin_handle.get_tenant_id(TENANT)
    #FER pglib_client = os_client.PGLib(PG_IP, PG_USER, PG_PASSWORD)

    # Get network A config
    neta_dict = api_helper.get_config_section(CONF, "NetworkA")
    (net_a_name, subnet_a_cidr,
     subnet_a_pool_start, subnet_a_pool_end,
     subnet_a_gateway, subnet_a_host_routes) = api_helper.network_config("NetworkA", neta_dict)

    # Get network B config
    netb_dict = api_helper.get_config_section(CONF, "NetworkB")
    (net_b_name, subnet_b_cidr,
     subnet_b_pool_start, subnet_b_pool_end,
     subnet_b_gateway, subnet_b_host_routes) = api_helper.network_config("NetworkB", netb_dict)

    # Get network C config
    netc_dict = api_helper.get_config_section(CONF, "NetworkC")
    (net_c_name, subnet_c_cidr,
     subnet_c_pool_start, subnet_c_pool_end,
     subnet_c_gateway, subnet_c_host_routes) = api_helper.network_config("NetworkC", netc_dict)

    # Get network D config
    netd_dict = api_helper.get_config_section(CONF, "NetworkD")
    (net_d_name, subnet_d_cidr,
     subnet_d_pool_start, subnet_d_pool_end,
     subnet_d_gateway, subnet_d_host_routes) = api_helper.network_config("NetworkD", netd_dict)

    # Get router C config
    routerc_dict = api_helper.get_config_section(CONF, "RouterC")
    (router_c_name, router_c_port_ip, router_c_dr) = api_helper.router_config("RouterC", routerc_dict)

    # Get router D config
    routerd_dict = api_helper.get_config_section(CONF, "RouterD")
    (router_d_name, router_d_port_ip, router_d_dr) = api_helper.router_config("RouterD", routerd_dict)

#FER 
#    print "Loading WIRE configuration"
#
#    existing_config = api_helper.get_config_section(CONF, "Link")
#    admin_vd = api_helper.element("infrastructure_vd", existing_config)
#    if admin_vd:
#        print "Management/Internet VD UUID found as: " + admin_vd
#    else:
#        admin_vd = api_helper.get_input("Enter the UUID of Internet or Management user")
#
#    router_id = api_helper.element("router_id", existing_config)
#   if router_id:
#       print "Interner/Management VD Router UUID found as: " + router_id
#   else:
#       router_id = api_helper.get_input("Enter Router UUID")
#
#   rtr_ifc_ip = api_helper.element("router_ifc_ip", existing_config)
#   if rtr_ifc_ip and api_helper.ip_in_cidr(rtr_ifc_ip, subnet_a_cidr):
#       print "Router interface IP found as: " + rtr_ifc_ip
#   else:
#       rtr_ifc_ip = api_helper.get_ip("Enter Router interface IP", subnet_a_cidr)




    flavor_list = tenant_handle.flavor_list()
    image_list = tenant_handle.image_list()
    net_list = ["a", "b", "c", "d"]

    # Get VM1 config
    vm1_dict = api_helper.get_config_section(CONF, "VM1")
    (vm1_name, vm1_flavor, vm1_image, vm1_cd, vm1_files, vm1_ips, vm1_userdata, vm1_meta) = api_helper.vm_config("VM1", vm1_dict, flavor_list, image_list, net_list)

    # Get VM2 config
    vm2_dict = api_helper.get_config_section(CONF, "VM2")
    (vm2_name, vm2_flavor, vm2_image, vm2_cd, vm2_files, vm2_ips, vm2_userdata, vm2_meta) = api_helper.vm_config("VM2", vm2_dict, flavor_list, image_list, net_list)

    # Get VM3 config
    vm3_dict = api_helper.get_config_section(CONF, "VM3")
    (vm3_name, vm3_flavor, vm3_image, vm3_cd, vm3_files, vm3_ips, vm3_userdata, vm3_meta) = api_helper.vm_config("VM3", vm3_dict, flavor_list, image_list, net_list)

    # Get VM4 config
    vm4_dict = api_helper.get_config_section(CONF, "VM4")
    (vm4_name, vm4_flavor, vm4_image, vm4_cd, vm4_files, vm4_ips, vm4_userdata, vm4_meta) = api_helper.vm_config("VM4", vm4_dict, flavor_list, image_list, net_list)

    # Get VM5 config
    vm5_dict = api_helper.get_config_section(CONF, "VM5")
    (vm5_name, vm5_flavor, vm5_image, vm5_cd, vm5_files, vm5_ips, vm5_userdata, vm5_meta) = api_helper.vm_config("VM5", vm5_dict, flavor_list, image_list,net_list)

    # Get VM6 config
    vm6_dict = api_helper.get_config_section(CONF, "VM6")
    (vm6_name, vm6_flavor, vm6_image, vm6_cd, vm6_files, vm6_ips, vm6_userdata, vm6_meta) = api_helper.vm_config("VM6", vm6_dict, flavor_list, image_list,net_list)

    # Get VM7 config
    vm7_dict = api_helper.get_config_section(CONF, "VM7")
    (vm7_name, vm7_flavor, vm7_image, vm7_cd, vm7_files, vm7_ips, vm7_userdata, vm7_meta) = api_helper.vm_config("VM7", vm7_dict, flavor_list, image_list,net_list)

    # Get VM8 config
    vm8_dict = api_helper.get_config_section(CONF, "VM8")
    (vm8_name, vm8_flavor, vm8_image, vm8_cd, vm8_files, vm8_ips, vm8_userdata, vm8_meta) = api_helper.vm_config("VM8", vm8_dict, flavor_list, image_list,net_list)

    # Get VM9 config
    vm9_dict = api_helper.get_config_section(CONF, "VM9")
    (vm9_name, vm9_flavor, vm9_image, vm9_cd, vm9_files, vm9_ips, vm9_userdata, vm9_meta) = api_helper.vm_config("VM9", vm9_dict, flavor_list, image_list,net_list)

    # Get VM10 config
    vm10_dict = api_helper.get_config_section(CONF, "VM10")
    (vm10_name, vm10_flavor, vm10_image, vm10_cd, vm10_files, vm10_ips, vm10_userdata, vm10_meta) = api_helper.vm_config("VM10", vm10_dict, flavor_list, image_list,net_list)

    # Get VM11 config
    vm11_dict = api_helper.get_config_section(CONF, "VM11")
    (vm11_name, vm11_flavor, vm11_image, vm11_cd, vm11_files, vm11_ips, vm11_userdata, vm11_meta) = api_helper.vm_config("VM11", vm11_dict, flavor_list, image_list,net_list)

    # Get VM12 config
    vm12_dict = api_helper.get_config_section(CONF, "VM12")
    (vm12_name, vm12_flavor, vm12_image, vm12_cd, vm12_files, vm12_ips, vm12_userdata, vm12_meta) = api_helper.vm_config("VM12", vm12_dict, flavor_list, image_list,net_list)

    # Get VM13 config
    vm13_dict = api_helper.get_config_section(CONF, "VM13")
    (vm13_name, vm13_flavor, vm13_image, vm13_cd, vm13_files, vm13_ips, vm13_userdata, vm13_meta) = api_helper.vm_config("VM13", vm13_dict, flavor_list, image_list,net_list)


    tenant_id = admin_handle.get_tenant_id(TENANT)

     # Create Network-A
    print "Creating Network: " + net_a_name
    net_a = tenant_handle.create_network(net_a_name)

    #time.sleep(5)

    # Create Subnet-A
    sub_a = tenant_handle.create_subnet(net_a["network"]["id"], subnet_a_cidr,
                                        subnet_a_pool_start, subnet_a_pool_end,
                                        subnet_a_gateway, True, subnet_a_host_routes)

    #time.sleep(5)

    # Create Network-B
    print "Creating Network: " + net_b_name
    net_b = tenant_handle.create_network(net_b_name)

    #time.sleep(5)

    # Create Subnet-B
    sub_b = tenant_handle.create_subnet(net_b["network"]["id"], subnet_b_cidr,
                                        subnet_b_pool_start, subnet_b_pool_end,
                                        subnet_b_gateway, True, subnet_b_host_routes)

    #time.sleep(5)

    # Create Network-C
    print "Creating Network: " + net_c_name
    net_c = tenant_handle.create_network(net_c_name)

    #time.sleep(5)

    # Create Subnet-C
    sub_c = tenant_handle.create_subnet(net_c["network"]["id"], subnet_c_cidr,
                                        subnet_c_pool_start, subnet_c_pool_end,
                                        subnet_c_gateway, True, subnet_c_host_routes)

    #time.sleep(5)


     # Create Network-D
    print "Creating Network: " + net_d_name
    net_d = tenant_handle.create_network(net_d_name)

    #time.sleep(5)

    # Create Subnet-D
    sub_d = tenant_handle.create_subnet(net_d["network"]["id"], subnet_d_cidr,
                                        subnet_d_pool_start, subnet_d_pool_end,
                                        subnet_d_gateway, True, subnet_d_host_routes)

    #time.sleep(5)

    # Create RouterC
    print "Creating Router: " + router_c_name
    router_c = tenant_handle.create_router(router_c_name)

    # Add default route
#FER    if router_c_dr:
#        pglib_client.add_route(tenant_id, router_c["router"]["id"],
#                               "default", router_c_dr, "0.0.0.0", "0.0.0.0")

    port = tenant_handle.add_network_port(router_c_port_ip, net_c["network"]["id"], sub_c["subnet"]["id"])
    print port

    tenant_handle.add_port_router(router_c["router"]["id"], port["port"]["id"])


    # Create RouterD
    print "Creating Router: " + router_d_name
    router_d = tenant_handle.create_router(router_d_name)

    # Add default route
#FER    if router_d_dr:
#        pglib_client.add_route(tenant_id, router_d["router"]["id"],
#                               "default", router_d_dr, "0.0.0.0", "0.0.0.0")

    port = tenant_handle.add_network_port(router_d_port_ip, net_d["network"]["id"], sub_d["subnet"]["id"])
    print port

    tenant_handle.add_port_router(router_d["router"]["id"], port["port"]["id"])


    time.sleep(5)

    # WIRE creation - MGMT
#    print "Creating MGMT WIRE!"
#    pglib_client.attach_to_tenant(tenant_id, router_id, rtr_ifc_ip, subnet_a_cidr, admin_vd, net_a["network"]["id"])

    time.sleep(5)


    # Launch VM1
    print "Launching vm: " + vm1_name
    net_list = [{"net": net_a["network"]["id"], "ip": vm1_ips["a"]}, {"net": net_b["network"]["id"], "ip": vm1_ips["b"]}, {"net": net_d["network"]["id"], "ip": vm1_ips["d"]}]
    tenant_handle.create_vm(vm1_name, net_list, vm1_image, vm1_flavor, vm1_cd, vm1_files, vm1_userdata, vm1_meta)

    time.sleep(5)

    # Launch VM2
    print "Launching vm: " + vm2_name
    net_list = [{"net": net_a["network"]["id"], "ip": vm2_ips["a"]}, {"net": net_b["network"]["id"], "ip": vm2_ips["b"]}, {"net": net_d["network"]["id"], "ip": vm2_ips["d"]}]
    tenant_handle.create_vm(vm2_name, net_list, vm2_image, vm2_flavor, vm2_cd, vm2_files, vm2_userdata, vm2_meta)

    time.sleep(5)

    # Launch VM3
    print "Launching vm: " + vm3_name
    net_list = [{"net": net_a["network"]["id"], "ip": vm3_ips["a"]}, {"net": net_d["network"]["id"], "ip": vm3_ips["d"]}]
    tenant_handle.create_vm(vm3_name, net_list, vm3_image, vm3_flavor, vm3_cd, vm3_files, vm3_userdata, vm3_meta)

    time.sleep(5)

    # Launch VM4
    print "Launching vm: " + vm4_name
    net_list = [{"net": net_a["network"]["id"], "ip": vm4_ips["a"]}, {"net": net_d["network"]["id"], "ip": vm4_ips["d"]}]
    tenant_handle.create_vm(vm4_name, net_list, vm4_image, vm4_flavor, vm4_cd, vm4_files, vm4_userdata, vm4_meta)

    time.sleep(5)

    # Launch VM5
    print "Launching vm: " + vm5_name
    net_list = [{"net": net_c["network"]["id"], "ip": vm5_ips["c"]}, {"net": net_d["network"]["id"], "ip": vm5_ips["d"]}]
    tenant_handle.create_vm(vm5_name, net_list, vm5_image, vm5_flavor, vm5_cd, vm5_files, vm5_userdata, vm5_meta)

    time.sleep(5)

    # Launch VM6
    print "Launching vm: " + vm6_name
    net_list = [{"net": net_c["network"]["id"], "ip": vm6_ips["c"]}, {"net": net_d["network"]["id"], "ip": vm6_ips["d"]}]
    tenant_handle.create_vm(vm6_name, net_list, vm6_image, vm6_flavor, vm6_cd, vm6_files, vm6_userdata, vm6_meta)

    time.sleep(5)

    # Launch VM7
    print "Launching vm: " + vm7_name
    net_list = [{"net": net_c["network"]["id"], "ip": vm7_ips["c"]}, {"net": net_d["network"]["id"], "ip": vm7_ips["d"]}]
    tenant_handle.create_vm(vm7_name, net_list, vm7_image, vm7_flavor, vm7_cd, vm7_files, vm7_userdata, vm7_meta)

    time.sleep(5)

    # Launch VM8
    print "Launching vm: " + vm8_name
    net_list = [{"net": net_c["network"]["id"], "ip": vm8_ips["c"]}, {"net": net_d["network"]["id"], "ip": vm8_ips["d"]}]
    tenant_handle.create_vm(vm8_name, net_list, vm8_image, vm8_flavor, vm8_cd, vm8_files, vm8_userdata, vm8_meta)

    time.sleep(5)

    # Launch VM9
    print "Launching vm: " + vm9_name
    net_list = [{"net": net_c["network"]["id"], "ip": vm9_ips["c"]}, {"net": net_d["network"]["id"], "ip": vm9_ips["d"]}]
    tenant_handle.create_vm(vm9_name, net_list, vm9_image, vm9_flavor, vm9_cd, vm9_files, vm9_userdata, vm9_meta)

    time.sleep(5)

    # Launch VM10
    print "Launching vm: " + vm10_name
    net_list = [{"net": net_c["network"]["id"], "ip": vm10_ips["c"]}, {"net": net_d["network"]["id"], "ip": vm10_ips["d"]}]
    tenant_handle.create_vm(vm10_name, net_list, vm10_image, vm10_flavor, vm10_cd, vm10_files, vm10_userdata, vm10_meta)

    time.sleep(5)

    # Launch VM11
    print "Launching vm: " + vm11_name
    net_list = [{"net": net_c["network"]["id"], "ip": vm11_ips["c"]}, {"net": net_d["network"]["id"], "ip": vm11_ips["d"]}]
    tenant_handle.create_vm(vm11_name, net_list, vm11_image, vm11_flavor, vm11_cd, vm11_files, vm11_userdata, vm11_meta)

    time.sleep(5)

    # Launch VM12
    print "Launching vm: " + vm12_name
    net_list = [{"net": net_c["network"]["id"], "ip": vm12_ips["c"]}, {"net": net_d["network"]["id"], "ip": vm12_ips["d"]}]
    tenant_handle.create_vm(vm12_name, net_list, vm12_image, vm12_flavor, vm12_cd, vm12_files, vm12_userdata, vm12_meta)

    # Launch VM13
    print "Launching vm: " + vm13_name
    net_list = [{"net": net_c["network"]["id"], "ip": vm13_ips["c"]}, {"net": net_e["network"]["id"], "ip": vm13_ips["e"]}]
    tenant_handle.create_vm(vm13_name, net_list, vm13_image, vm13_flavor, vm13_cd, vm13_files, vm13_userdata, vm1r_meta)

print "Successfully deployed."
