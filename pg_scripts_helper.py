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

import ipaddr
import ConfigParser
import sys
import json

"""
Helper routines for deployment scripts
"""

def load_config_file(file_name):
    config = ConfigParser.ConfigParser()
    config.read(file_name)
    return config

def get_config_section(config_file, section_name):
    try:
        conf = load_config_file(config_file)
        return dict(conf.items(section_name))
    except ConfigParser.NoSectionError:
        return {}

def check_config_section(config_file, section_name):
    try:
        conf = load_config_file(config_file)
        return dict(conf.items(section_name))
    except ConfigParser.NoSectionError:
        return None

def get_input(input_desc):
    output = ""
    while True:
        if output:
            break
        output = raw_input("\n" + input_desc +": ")
    return output

def valid_vlan_tag(vlan):
    try:
        return (1 <= int(vlan) <= 4094)
    except:
        return False

def valid_cidr(cidr):
    try:
        ipaddr.IPNetwork(cidr)
        return True
    except ValueError:
        return False

def ip_in_cidr(ip, cidr):
    try:
        return ipaddr.IPAddress(ip) in ipaddr.IPNetwork(cidr)
    except ValueError:
        return False

def valid_ifc_name(ifc):
    host_ifc = ifc.split("+")
    try:
        host_split_check = host_ifc[2]
        return False
    except IndexError:
        pass
    try:
        hostname = host_ifc[0]
        device_name = host_ifc[1]
        return True
    except:
        return False

def get_ip(message, cidr):
    while True:
        ip = raw_input("\n" + message + ": ")
        if ip_in_cidr(ip, cidr):
            return ip
        print "\n*Invalid Entry: IP Address not in the subnet.*"

def get_cidr(message):
    while True:
        cidr = raw_input("\n" + message + ": ")
        if valid_cidr(cidr):
            return cidr
        print "\n *Invalid CIDR (" + cidr + "). Please enter a valid value.*"

def get_vlan(message):
    while True:
        vlan_id = raw_input("\n" + message + ": ")
        if valid_vlan_tag(vlan_id):
            return vlan_id
        print "\n*Invalid VLAN ID (" + vlan_id + ")"

def get_phy_net(message):
    while True:
        phy_net = raw_input("\n" + message +
                            "(plumgrid-gateway-hostname+interface_name): ")
        if valid_ifc_name(phy_net):
            return phy_net
        print "\n*Invalid hostname+ifc (" + phy_net + ")*"

def element(element, dictry):
    if element in dictry and element:
        return dictry[element]
    else:
        return None


def provider_network_config(name, existing_data):
    net_name = element("name", existing_data)
    if net_name:
        print name+ "name found as: " + net_name
    else:
        net_name = get_input(name + " Name")

    net_type = element("type", existing_data)
    if net_type and net_type.lower() in ["flat", "vlan"]:
        print name + " type found as: " + net_type
    else:
        net_type = ""
        while True:
            if net_type.lower() in ["flat", "vlan"]:
                break
            net_type = raw_input("\n"+name+" provider type(vlan/flat): ")

    vlan_id = element("vlan_id", existing_data)
    if net_type == "vlan":
        if vlan_id and valid_vlan_tag(vlan_id):
            print name +" vlan id found as: " + vlan_id
        else:
            vlan_id = get_vlan(name+ " VLAN ID(1-4094)")

    physical_network = element("physical_network", existing_data)
    if physical_network and valid_ifc_name(physical_network):
        print name + " physical network found as: " + physical_network
    else:
        physical_network = get_phy_net(name + " provider physical network")

    cidr = element("cidr", existing_data)
    if cidr and valid_cidr(cidr):
        name + " cidr found as: " + cidr
    else:
        cidr = get_cidr(name + " subnet CIDR")


    pool_start = element("pool_start", existing_data)
    if pool_start and ip_in_cidr(pool_start, cidr):
        print name + " subnet allocation pool start found as: " + pool_start
    else:
        pool_start = get_ip(name + " subnet allocation pool start", cidr)

    pool_end = element("pool_end", existing_data)
    if pool_end and ip_in_cidr(pool_end, cidr):
        print name + " subnet allocation pool end found as: " + pool_end
    else:
        pool_end = get_ip(name + " subnet allocation pool end", cidr)

    gateway = element("router_ip", existing_data)
    if gateway:
        if gateway and ip_in_cidr(gateway, cidr):
            print name + " subnet gateway ip found as: " + gateway
        else:
            gateway = get_ip(name + " subnet Gateway IP", cidr)

    return (net_name, net_type, vlan_id, physical_network, cidr, pool_start, pool_end, gateway)


def network_config(name, existing_data):
    net_name = element("name", existing_data)
    if net_name:
        print name+ "name found as: " + net_name
    else:
        net_name = get_input(name + " Name")

    cidr = element("cidr", existing_data)
    if cidr and valid_cidr(cidr):
        name + " cidr found as: " + cidr
    else:
        cidr = get_cidr(name + " subnet CIDR")


    pool_start = element("pool_start", existing_data)
    if pool_start and ip_in_cidr(pool_start, cidr):
        print name + " subnet allocation pool start found as: " + pool_start
    else:
        pool_start = get_ip(name + " subnet allocation pool start", cidr)

    pool_end = element("pool_end", existing_data)
    if pool_end and ip_in_cidr(pool_end, cidr):
        print name + " subnet allocation pool end found as: " + pool_end
    else:
        pool_end = get_ip(name + " subnet allocation pool end", cidr)

    host_routes = None
    host_routes_str = element("host_routes", existing_data)
    if host_routes_str:
        host_routes = json.loads(host_routes_str)
        print host_routes

    gateway = element("router_ip", existing_data)
    print "gateway: " + gateway    

    if gateway == "null":
        print "null"
    elif gateway == None:
        print "None"
    elif gateway and ip_in_cidr(gateway, cidr):
        print name + " subnet gateway ip found as: " + gateway
    else:
        gateway = get_ip(name + " subnet Gateway IP", cidr)

    return (net_name, cidr, pool_start, pool_end, gateway, host_routes)

def router_config(name, existing_data):
    router_name = element("name", existing_data)
    if router_name:
        print name + " name found as: " + router_name
    else:
        router_name = get_input(name + " Name")

    default_route = element("default_route_ip", existing_data)
    if default_route:
        print name + "default route found: " + default_route
    else:
        default_route = None

    port_ip = element("port_ip", existing_data)

    return (router_name, port_ip, default_route)


def vm_config(name, existing_data, flavor_list, image_list, net_list):
    vm_name = element("name", existing_data)
    if vm_name:
        print name + " name found as: " + vm_name
    else:
        vm_name = get_input(name + " Name")

    vm_flavor = element("flavor", existing_data)
    if vm_flavor:
        print name + " flavor found as: " + vm_flavor
    else:
        vm_flavor = api_helper.get_input("Enter " + name + " flavor name" + str(flavor_list)  + ":")

    vm_image = element("image", existing_data)
    if vm_flavor:
        print name + " image found as: " + vm_image
    else:
        vm_image = api_helper.get_input("Enter " + name + " image name" + str(image_list)  + ":")

    cd = element("metadata_inject", existing_data)
    if not cd:
        cd = False

    conf_files = element("files", existing_data)
    if conf_files:
        files = _get_config_files(conf_files)
    else:
        files = None

    ips = {}
    for net in net_list:
        ip = element("ip_net_" + net, existing_data)
        if ip:
            ips[net] = ip

    userdata = None
    cf_source = element("userdata", existing_data)
    if cf_source:
        with open(cf_source, 'r') as content_file:
            userdata = content_file.read()

    meta = None
    metastr = element("meta", existing_data)
    if metastr:
        meta = json.loads(metastr)

    return (vm_name, vm_flavor, vm_image, cd, files, ips, userdata, meta)

def get_config_item(config, existing_conf, arg):
    if element(config, existing_conf) and arg is None:
        USERNAME = element(config, existing_conf)
    elif arg:
        USERNAME = arg
    else:
        raise Exception("Parameter: " + config + " is missing")
    return USERNAME

def _get_config_files(files):
    try:
        cf = files.split(",")
        i = len(cf)
        file_list = {}
        for x in range(0, i):
            cf_internal = cf[x].split(":")
            cf_target = cf_internal[0]
            cf_source = cf_internal[1]
            if cf_target and cf_source:
                with open(cf_source, 'r') as content_file:
                    content = content_file.read()
            file_list[cf_target] = content
        print "Config files: "+ str(file_list)
        return file_list
    except:
        raise
