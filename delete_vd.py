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
import tenant_cleanup
import os_client
import pg_scripts_helper as api_helper

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Delete virtual domain')


    parser = argparse.ArgumentParser(description='Create Internet Virtual Domain')

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

    admin_handle = os_client.OSClient(AUTH_URL, ADMIN_USER, ADMIN_TENANT, ADMIN_PASSWORD)
    tenant_id = admin_handle.get_tenant_id(TENANT)

    cleanup_handle = tenant_cleanup.OpenStackCleanup(USERNAME, PASSWORD, TENANT, AUTH_URL, PG_IP, "443", 70, PG_USER, PG_PASSWORD, True)
    cleanup_handle.open_stack_cleanup(TENANT, tenant_id)
