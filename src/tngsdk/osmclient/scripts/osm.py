# Copyright 2017-2018 Sandvine
# Copyright 2018 Telefonica
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
OSM shell/cli
"""

import click
from osmclient import client
from osmclient.common.exceptions import ClientException
from prettytable import PrettyTable
import yaml
import json
import time
import pycurl


def check_client_version(obj, what, version='sol005'):
    """
    Checks the version of the client object and raises error if it not the expected.

    :param obj: the client object
    :what: the function or command under evaluation (used when an error is raised)
    :return: -
    :raises ClientError: if the specified version does not match the client version
    """
    fullclassname = obj.__module__ + "." + obj.__class__.__name__
    message = 'The following commands or options are only supported with the option "--sol005": {}'.format(what)
    if version == 'v1':
        message = 'The following commands or options are not supported when using option "--sol005": {}'.format(what)
    if fullclassname != 'osmclient.{}.client.Client'.format(version):
        raise ClientException(message)
    return


@click.group()
@click.option('--hostname',
              default="127.0.0.1",
              envvar='OSM_HOSTNAME',
              help='hostname of server.  ' +
                   'Also can set OSM_HOSTNAME in environment')
@click.option('--sol005/--no-sol005',
              default=True,
              envvar='OSM_SOL005',
              help='Use ETSI NFV SOL005 API (default) or the previous SO API. ' +
                   'Also can set OSM_SOL005 in environment')
@click.option('--user',
              default=None,
              envvar='OSM_USER',
              help='user (only from Release FOUR, defaults to admin). ' +
                   'Also can set OSM_USER in environment')
@click.option('--password',
              default=None,
              envvar='OSM_PASSWORD',
              help='password (only from Release FOUR, defaults to admin). ' +
                   'Also can set OSM_PASSWORD in environment')
@click.option('--project',
              default=None,
              envvar='OSM_PROJECT',
              help='project (only from Release FOUR, defaults to admin). ' +
                   'Also can set OSM_PROJECT in environment')
@click.option('--so-port',
              default=None,
              envvar='OSM_SO_PORT',
              help='hostname of server.  ' +
                   'Also can set OSM_SO_PORT in environment')
@click.option('--so-project',
              default=None,
              envvar='OSM_SO_PROJECT',
              help='Project Name in SO.  ' +
                   'Also can set OSM_SO_PROJECT in environment')
@click.option('--ro-hostname',
              default=None,
              envvar='OSM_RO_HOSTNAME',
              help='hostname of RO server.  ' +
              'Also can set OSM_RO_HOSTNAME in environment')
@click.option('--ro-port',
              default=None,
              envvar='OSM_RO_PORT',
              help='hostname of RO server.  ' +
                   'Also can set OSM_RO_PORT in environment')
@click.pass_context
def cli(ctx, hostname, sol005, user, password, project, so_port, so_project, ro_hostname, ro_port):
    if hostname is None:
        print((
            "either hostname option or OSM_HOSTNAME " +
            "environment variable needs to be specified"))
        exit(1)
    kwargs={}
    if so_port is not None:
        kwargs['so_port']=so_port
    if so_project is not None:
        kwargs['so_project']=so_project
    if ro_hostname is not None:
        kwargs['ro_host']=ro_hostname
    if ro_port is not None:
        kwargs['ro_port']=ro_port
    if user is not None:
        kwargs['user']=user
    if password is not None:
        kwargs['password']=password
    if project is not None:
        kwargs['project']=project

    ctx.obj = client.Client(host=hostname, sol005=sol005, **kwargs)


####################
# LIST operations
####################

@cli.command(name='ns-list')
@click.option('--filter', default=None,
              help='restricts the list to the NS instances matching the filter.')
@click.pass_context
def ns_list(ctx, filter):
    """list all NS instances

    \b
    Options:
      --filter filterExpr    Restricts the list to the NS instances matching the filter

    \b
    filterExpr consists of one or more strings formatted according to "simpleFilterExpr",
    concatenated using the "&" character:

      \b
      filterExpr := <simpleFilterExpr>["&"<simpleFilterExpr>]*
      simpleFilterExpr := <attrName>["."<attrName>]*["."<op>]"="<value>[","<value>]*
      op := "eq" | "neq" | "gt" | "lt" | "gte" | "lte" | "cont" | "ncont"
      attrName := string
      value := scalar value

    \b
    where:
      * zero or more occurrences
      ? zero or one occurrence
      [] grouping of expressions to be used with ? and *
      "" quotation marks for marking string constants
      <> name separator

    \b
    "AttrName" is the name of one attribute in the data type that defines the representation
    of the resource. The dot (".") character in "simpleFilterExpr" allows concatenation of
    <attrName> entries to filter by attributes deeper in the hierarchy of a structured document.
    "Op" stands for the comparison operator. If the expression has concatenated <attrName>
    entries, it means that the operator "op" is applied to the attribute addressed by the last
    <attrName> entry included in the concatenation. All simple filter expressions are combined
    by the "AND" logical operator. In a concatenation of <attrName> entries in a <simpleFilterExpr>,
    the rightmost "attrName" entry in a "simpleFilterExpr" is called "leaf attribute". The
    concatenation of all "attrName" entries except the leaf attribute is called the "attribute
    prefix". If an attribute referenced in an expression is an array, an object that contains a
    corresponding array shall be considered to match the expression if any of the elements in the
    array matches all expressions that have the same attribute prefix.

    \b
    Filter examples:
       --filter  admin-status=ENABLED
       --filter  nsd-ref=<NSD_NAME>
       --filter  nsd.vendor=<VENDOR>
       --filter  nsd.vendor=<VENDOR>&nsd-ref=<NSD_NAME>
       --filter  nsd.constituent-vnfd.vnfd-id-ref=<VNFD_NAME>
    """
    if filter:
        check_client_version(ctx.obj, '--filter')
        resp = ctx.obj.ns.list(filter)
    else:
        resp = ctx.obj.ns.list()
    table = PrettyTable(
        ['ns instance name',
         'id',
         'operational status',
         'config status',
         'detailed status'])
    for ns in resp:
        fullclassname = ctx.obj.__module__ + "." + ctx.obj.__class__.__name__
        if fullclassname == 'osmclient.sol005.client.Client':
            nsr = ns
            nsr_name = nsr['name']
            nsr_id = nsr['_id']
        else:
            nsopdata = ctx.obj.ns.get_opdata(ns['id'])
            nsr = nsopdata['nsr:nsr']
            nsr_name = nsr['name-ref']
            nsr_id = nsr['ns-instance-config-ref']
        opstatus = nsr['operational-status'] if 'operational-status' in nsr else 'Not found'
        configstatus = nsr['config-status'] if 'config-status' in nsr else 'Not found'
        detailed_status = nsr['detailed-status'] if 'detailed-status' in nsr else 'Not found'
        if configstatus == "config_not_needed":
            configstatus = "configured (no charms)"
        table.add_row(
            [nsr_name,
             nsr_id,
             opstatus,
             configstatus,
             detailed_status])
    table.align = 'l'
    print(table)


def nsd_list(ctx, filter):
    if filter:
        check_client_version(ctx.obj, '--filter')
        resp = ctx.obj.nsd.list(filter)
    else:
        resp = ctx.obj.nsd.list()
    # print yaml.safe_dump(resp)
    table = PrettyTable(['nsd name', 'id'])
    fullclassname = ctx.obj.__module__ + "." + ctx.obj.__class__.__name__
    if fullclassname == 'osmclient.sol005.client.Client':
        for ns in resp:
            name = ns['name'] if 'name' in ns else '-'
            table.add_row([name, ns['_id']])
    else:
        for ns in resp:
            table.add_row([ns['name'], ns['id']])
    table.align = 'l'
    print(table)


@cli.command(name='nsd-list')
@click.option('--filter', default=None,
              help='restricts the list to the NSD/NSpkg matching the filter')
@click.pass_context
def nsd_list1(ctx, filter):
    """list all NSD/NS pkg in the system"""
    nsd_list(ctx, filter)


@cli.command(name='nspkg-list')
@click.option('--filter', default=None,
              help='restricts the list to the NSD/NSpkg matching the filter')
@click.pass_context
def nsd_list2(ctx, filter):
    """list all NSD/NS pkg in the system"""
    nsd_list(ctx, filter)


def vnfd_list(ctx, nf_type, filter):
    if nf_type:
        check_client_version(ctx.obj, '--nf_type')
    elif filter:
        check_client_version(ctx.obj, '--filter')
    if nf_type:
        if nf_type == "vnf":
            nf_filter = "_admin.type=vnfd"
        elif nf_type == "pnf":
            nf_filter = "_admin.type=pnfd"
        elif nf_type == "hnf":
            nf_filter = "_admin.type=hnfd"
        else:
            raise ClientException('wrong value for "--nf_type" option, allowed values: vnf, pnf, hnf')
        if filter:
            filter = '{}&{}'.format(nf_filter, filter)
        else:
            filter = nf_filter
    if filter:
        resp = ctx.obj.vnfd.list(filter)
    else:
        resp = ctx.obj.vnfd.list()
    # print yaml.safe_dump(resp)
    table = PrettyTable(['nfpkg name', 'id'])
    fullclassname = ctx.obj.__module__ + "." + ctx.obj.__class__.__name__
    if fullclassname == 'osmclient.sol005.client.Client':
        for vnfd in resp:
            name = vnfd['name'] if 'name' in vnfd else '-'
            table.add_row([name, vnfd['_id']])
    else:
        for vnfd in resp:
            table.add_row([vnfd['name'], vnfd['id']])
    table.align = 'l'
    print(table)


@cli.command(name='vnfd-list')
@click.option('--nf_type', help='type of NF (vnf, pnf, hnf)')
@click.option('--filter', default=None,
              help='restricts the list to the NF pkg matching the filter')
@click.pass_context
def vnfd_list1(ctx, nf_type, filter):
    """list all VNFD/VNF pkg in the system"""
    vnfd_list(ctx, nf_type, filter)


@cli.command(name='vnfpkg-list')
@click.option('--nf_type', help='type of NF (vnf, pnf, hnf)')
@click.option('--filter', default=None,
              help='restricts the list to the NFpkg matching the filter')
@click.pass_context
def vnfd_list2(ctx, nf_type, filter):
    """list all VNFD/VNF pkg in the system"""
    vnfd_list(ctx, nf_type, filter)


@cli.command(name='nfpkg-list')
@click.option('--nf_type', help='type of NF (vnf, pnf, hnf)')
@click.option('--filter', default=None,
              help='restricts the list to the NFpkg matching the filter')
@click.pass_context
def nfpkg_list(ctx, nf_type, filter):
    """list all NF pkg (VNF pkg, PNF pkg, HNF pkg) in the system"""
    try:
        check_client_version(ctx.obj, ctx.command.name)
        vnfd_list(ctx, nf_type, filter)
    except ClientException as inst:
        print((inst.message))
        exit(1)


def vnf_list(ctx, ns, filter):
    try:
        if ns or filter:
            if ns:
                check_client_version(ctx.obj, '--ns')
            if filter:
                check_client_version(ctx.obj, '--filter')
            resp = ctx.obj.vnf.list(ns, filter)
        else:
            resp = ctx.obj.vnf.list()
    except ClientException as inst:
        print((inst.message))
        exit(1)
    fullclassname = ctx.obj.__module__ + "." + ctx.obj.__class__.__name__
    if fullclassname == 'osmclient.sol005.client.Client':
        table = PrettyTable(
            ['vnf id',
             'name',
             'ns id',
             'vnf member index',
             'vnfd name',
             'vim account id',
             'ip address'])
        for vnfr in resp:
            name = vnfr['name'] if 'name' in vnfr else '-'
            table.add_row(
                [vnfr['_id'],
                 name,
                 vnfr['nsr-id-ref'],
                 vnfr['member-vnf-index-ref'],
                 vnfr['vnfd-ref'],
                 vnfr['vim-account-id'],
                 vnfr['ip-address']])
    else:
        table = PrettyTable(
            ['vnf name',
             'id',
             'operational status',
             'config status'])
        for vnfr in resp:
            if 'mgmt-interface' not in vnfr:
                vnfr['mgmt-interface'] = {}
                vnfr['mgmt-interface']['ip-address'] = None
            table.add_row(
                [vnfr['name'],
                 vnfr['id'],
                 vnfr['operational-status'],
                 vnfr['config-status']])
    table.align = 'l'
    print(table)


@cli.command(name='vnf-list')
@click.option('--ns', default=None, help='NS instance id or name to restrict the NF list')
@click.option('--filter', default=None,
              help='restricts the list to the NF instances matching the filter.')
@click.pass_context
def vnf_list1(ctx, ns, filter):
    """list all NF instances"""
    vnf_list(ctx, ns, filter)


@cli.command(name='nf-list')
@click.option('--ns', default=None, help='NS instance id or name to restrict the NF list')
@click.option('--filter', default=None,
              help='restricts the list to the NF instances matching the filter.')
@click.pass_context
def nf_list(ctx, ns, filter):
    """list all NF instances

    \b
    Options:
      --ns     TEXT           NS instance id or name to restrict the VNF list
      --filter filterExpr     Restricts the list to the VNF instances matching the filter

    \b
    filterExpr consists of one or more strings formatted according to "simpleFilterExpr",
    concatenated using the "&" character:

      \b
      filterExpr := <simpleFilterExpr>["&"<simpleFilterExpr>]*
      simpleFilterExpr := <attrName>["."<attrName>]*["."<op>]"="<value>[","<value>]*
      op := "eq" | "neq" | "gt" | "lt" | "gte" | "lte" | "cont" | "ncont"
      attrName := string
      value := scalar value

    \b
    where:
      * zero or more occurrences
      ? zero or one occurrence
      [] grouping of expressions to be used with ? and *
      "" quotation marks for marking string constants
      <> name separator

    \b
    "AttrName" is the name of one attribute in the data type that defines the representation
    of the resource. The dot (".") character in "simpleFilterExpr" allows concatenation of
    <attrName> entries to filter by attributes deeper in the hierarchy of a structured document.
    "Op" stands for the comparison operator. If the expression has concatenated <attrName>
    entries, it means that the operator "op" is applied to the attribute addressed by the last
    <attrName> entry included in the concatenation. All simple filter expressions are combined
    by the "AND" logical operator. In a concatenation of <attrName> entries in a <simpleFilterExpr>,
    the rightmost "attrName" entry in a "simpleFilterExpr" is called "leaf attribute". The
    concatenation of all "attrName" entries except the leaf attribute is called the "attribute
    prefix". If an attribute referenced in an expression is an array, an object that contains a
    corresponding array shall be considered to match the expression if any of the elements in the
    array matches all expressions that have the same attribute prefix.

    \b
    Filter examples:
       --filter  vim-account-id=<VIM_ACCOUNT_ID>
       --filter  vnfd-ref=<VNFD_NAME>
       --filter  vdur.ip-address=<IP_ADDRESS>
       --filter  vnfd-ref=<VNFD_NAME>,vdur.ip-address=<IP_ADDRESS>
    """
    vnf_list(ctx, ns, filter)


@cli.command(name='ns-op-list')
@click.argument('name')
@click.pass_context
def ns_op_list(ctx, name):
    """shows the history of operations over a NS instance

    NAME: name or ID of the NS instance
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.ns.list_op(name)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    table = PrettyTable(['id', 'operation', 'status'])
    for op in resp:
        table.add_row([op['id'], op['lcmOperationType'],
                       op['operationState']])
    table.align = 'l'
    print(table)


def nsi_list(ctx, filter):
    """list all Network Slice Instances"""
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.nsi.list(filter)
    except ClientException as inst:
        print((inst.message))
        exit(1)
    table = PrettyTable(
        ['netslice instance name',
         'id',
         'operational status',
         'config status',
         'detailed status'])
    for nsi in resp:
        nsi_name = nsi['name']
        nsi_id = nsi['_id']
        opstatus = nsi['operational-status'] if 'operational-status' in nsi else 'Not found'
        configstatus = nsi['config-status'] if 'config-status' in nsi else 'Not found'
        detailed_status = nsi['detailed-status'] if 'detailed-status' in nsi else 'Not found'
        if configstatus == "config_not_needed":
            configstatus = "configured (no charms)"
        table.add_row(
            [nsi_name,
             nsi_id,
             opstatus,
             configstatus,
             detailed_status])
    table.align = 'l'
    print(table)


@cli.command(name='nsi-list')
@click.option('--filter', default=None,
              help='restricts the list to the Network Slice Instances matching the filter')
@click.pass_context
def nsi_list1(ctx, filter):
    """list all Network Slice Instances (NSI)"""
    nsi_list(ctx, filter)


@cli.command(name='netslice-instance-list')
@click.option('--filter', default=None,
              help='restricts the list to the Network Slice Instances matching the filter')
@click.pass_context
def nsi_list2(ctx, filter):
    """list all Network Slice Instances (NSI)"""
    nsi_list(ctx, filter)


def nst_list(ctx, filter):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.nst.list(filter)
    except ClientException as inst:
        print((inst.message))
        exit(1)
    # print yaml.safe_dump(resp)
    table = PrettyTable(['nst name', 'id'])
    for nst in resp:
        name = nst['name'] if 'name' in nst else '-'
        table.add_row([name, nst['_id']])
    table.align = 'l'
    print(table)


@cli.command(name='nst-list')
@click.option('--filter', default=None,
              help='restricts the list to the NST matching the filter')
@click.pass_context
def nst_list1(ctx, filter):
    """list all Network Slice Templates (NST) in the system"""
    nst_list(ctx, filter)


@cli.command(name='netslice-template-list')
@click.option('--filter', default=None,
              help='restricts the list to the NST matching the filter')
@click.pass_context
def nst_list2(ctx, filter):
    """list all Network Slice Templates (NST) in the system"""
    nst_list(ctx, filter)


def nsi_op_list(ctx, name):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.nsi.list_op(name)
    except ClientException as inst:
        print((inst.message))
        exit(1)
    table = PrettyTable(['id', 'operation', 'status'])
    for op in resp:
        table.add_row([op['id'], op['lcmOperationType'],
                       op['operationState']])
    table.align = 'l'
    print(table)


@cli.command(name='nsi-op-list')
@click.argument('name')
@click.pass_context
def nsi_op_list1(ctx, name):
    """shows the history of operations over a Network Slice Instance (NSI)

    NAME: name or ID of the Network Slice Instance
    """
    nsi_op_list(ctx, name)


@cli.command(name='netslice-instance-op-list')
@click.argument('name')
@click.pass_context
def nsi_op_list2(ctx, name):
    """shows the history of operations over a Network Slice Instance (NSI)

    NAME: name or ID of the Network Slice Instance
    """
    nsi_op_list(ctx, name)


@cli.command(name='pdu-list')
@click.option('--filter', default=None,
              help='restricts the list to the Physical Deployment Units matching the filter')
@click.pass_context
def pdu_list(ctx, filter):
    """list all Physical Deployment Units (PDU)"""
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.pdu.list(filter)
    except ClientException as inst:
        print((inst.message))
        exit(1)
    table = PrettyTable(
        ['pdu name',
         'id',
         'type',
         'mgmt ip address'])
    for pdu in resp:
        pdu_name = pdu['name']
        pdu_id = pdu['_id']
        pdu_type = pdu['type']
        pdu_ipaddress = "None"
        for iface in pdu['interfaces']:
            if iface['mgmt']:
                pdu_ipaddress = iface['ip-address']
                break
        table.add_row(
            [pdu_name,
             pdu_id,
             pdu_type,
             pdu_ipaddress])
    table.align = 'l'
    print(table)


####################
# SHOW operations
####################

def nsd_show(ctx, name, literal):
    try:
        resp = ctx.obj.nsd.get(name)
        # resp = ctx.obj.nsd.get_individual(name)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    if literal:
        print(yaml.safe_dump(resp))
        return

    table = PrettyTable(['field', 'value'])
    for k, v in list(resp.items()):
        table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


@cli.command(name='nsd-show', short_help='shows the content of a NSD')
@click.option('--literal', is_flag=True,
              help='print literally, no pretty table')
@click.argument('name')
@click.pass_context
def nsd_show1(ctx, name, literal):
    """shows the content of a NSD

    NAME: name or ID of the NSD/NSpkg
    """
    nsd_show(ctx, name, literal)


@cli.command(name='nspkg-show', short_help='shows the content of a NSD')
@click.option('--literal', is_flag=True,
              help='print literally, no pretty table')
@click.argument('name')
@click.pass_context
def nsd_show2(ctx, name, literal):
    """shows the content of a NSD

    NAME: name or ID of the NSD/NSpkg
    """
    nsd_show(ctx, name, literal)


def vnfd_show(ctx, name, literal):
    try:
        resp = ctx.obj.vnfd.get(name)
        # resp = ctx.obj.vnfd.get_individual(name)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    if literal:
        print(yaml.safe_dump(resp))
        return

    table = PrettyTable(['field', 'value'])
    for k, v in list(resp.items()):
        table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


@cli.command(name='vnfd-show', short_help='shows the content of a VNFD')
@click.option('--literal', is_flag=True,
              help='print literally, no pretty table')
@click.argument('name')
@click.pass_context
def vnfd_show1(ctx, name, literal):
    """shows the content of a VNFD

    NAME: name or ID of the VNFD/VNFpkg
    """
    vnfd_show(ctx, name, literal)


@cli.command(name='vnfpkg-show', short_help='shows the content of a VNFD')
@click.option('--literal', is_flag=True,
              help='print literally, no pretty table')
@click.argument('name')
@click.pass_context
def vnfd_show2(ctx, name, literal):
    """shows the content of a VNFD

    NAME: name or ID of the VNFD/VNFpkg
    """
    vnfd_show(ctx, name, literal)


@cli.command(name='nfpkg-show', short_help='shows the content of a NF Descriptor')
@click.option('--literal', is_flag=True,
              help='print literally, no pretty table')
@click.argument('name')
@click.pass_context
def nfpkg_show(ctx, name, literal):
    """shows the content of a NF Descriptor

    NAME: name or ID of the NFpkg
    """
    vnfd_show(ctx, name, literal)


@cli.command(name='ns-show', short_help='shows the info of a NS instance')
@click.argument('name')
@click.option('--literal', is_flag=True,
              help='print literally, no pretty table')
@click.option('--filter', default=None)
@click.pass_context
def ns_show(ctx, name, literal, filter):
    """shows the info of a NS instance

    NAME: name or ID of the NS instance
    """
    try:
        ns = ctx.obj.ns.get(name)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    if literal:
        print(yaml.safe_dump(ns))
        return

    table = PrettyTable(['field', 'value'])

    for k, v in list(ns.items()):
        if filter is None or filter in k:
            table.add_row([k, json.dumps(v, indent=2)])

    fullclassname = ctx.obj.__module__ + "." + ctx.obj.__class__.__name__
    if fullclassname != 'osmclient.sol005.client.Client':
        nsopdata = ctx.obj.ns.get_opdata(ns['id'])
        nsr_optdata = nsopdata['nsr:nsr']
        for k, v in list(nsr_optdata.items()):
            if filter is None or filter in k:
                table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


@cli.command(name='vnf-show', short_help='shows the info of a VNF instance')
@click.argument('name')
@click.option('--literal', is_flag=True,
              help='print literally, no pretty table')
@click.option('--filter', default=None)
@click.pass_context
def vnf_show(ctx, name, literal, filter):
    """shows the info of a VNF instance

    NAME: name or ID of the VNF instance
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.vnf.get(name)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    if literal:
        print(yaml.safe_dump(resp))
        return

    table = PrettyTable(['field', 'value'])
    for k, v in list(resp.items()):
        if filter is None or filter in k:
            table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


@cli.command(name='vnf-monitoring-show')
@click.argument('vnf_name')
@click.pass_context
def vnf_monitoring_show(ctx, vnf_name):
    try:
        check_client_version(ctx.obj, ctx.command.name, 'v1')
        resp = ctx.obj.vnf.get_monitoring(vnf_name)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    table = PrettyTable(['vnf name', 'monitoring name', 'value', 'units'])
    if resp is not None:
        for monitor in resp:
            table.add_row(
                [vnf_name,
                 monitor['name'],
                    monitor['value-integer'],
                    monitor['units']])
    table.align = 'l'
    print(table)


@cli.command(name='ns-monitoring-show')
@click.argument('ns_name')
@click.pass_context
def ns_monitoring_show(ctx, ns_name):
    try:
        check_client_version(ctx.obj, ctx.command.name, 'v1')
        resp = ctx.obj.ns.get_monitoring(ns_name)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    table = PrettyTable(['vnf name', 'monitoring name', 'value', 'units'])
    for key, val in list(resp.items()):
        for monitor in val:
            table.add_row(
                [key,
                 monitor['name'],
                    monitor['value-integer'],
                    monitor['units']])
    table.align = 'l'
    print(table)


@cli.command(name='ns-op-show', short_help='shows the info of an operation')
@click.argument('id')
@click.option('--filter', default=None)
@click.pass_context
def ns_op_show(ctx, id, filter):
    """shows the detailed info of an operation

    ID: operation identifier
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        op_info = ctx.obj.ns.get_op(id)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    table = PrettyTable(['field', 'value'])
    for k, v in list(op_info.items()):
        if filter is None or filter in k:
            table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


def nst_show(ctx, name, literal):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.nst.get(name)
        #resp = ctx.obj.nst.get_individual(name)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    if literal:
        print(yaml.safe_dump(resp))
        return

    table = PrettyTable(['field', 'value'])
    for k, v in list(resp.items()):
        table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


@cli.command(name='nst-show', short_help='shows the content of a Network Slice Template (NST)')
@click.option('--literal', is_flag=True,
              help='print literally, no pretty table')
@click.argument('name')
@click.pass_context
def nst_show1(ctx, name, literal):
    """shows the content of a Network Slice Template (NST)

    NAME: name or ID of the NST
    """
    nst_show(ctx, name, literal)


@cli.command(name='netslice-template-show', short_help='shows the content of a Network Slice Template (NST)')
@click.option('--literal', is_flag=True,
              help='print literally, no pretty table')
@click.argument('name')
@click.pass_context
def nst_show2(ctx, name, literal):
    """shows the content of a Network Slice Template (NST)

    NAME: name or ID of the NST
    """
    nst_show(ctx, name, literal)


def nsi_show(ctx, name, literal, filter):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        nsi = ctx.obj.nsi.get(name)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    if literal:
        print(yaml.safe_dump(nsi))
        return

    table = PrettyTable(['field', 'value'])

    for k, v in list(nsi.items()):
        if filter is None or filter in k:
            table.add_row([k, json.dumps(v, indent=2)])

    table.align = 'l'
    print(table)


@cli.command(name='nsi-show', short_help='shows the content of a Network Slice Instance (NSI)')
@click.argument('name')
@click.option('--literal', is_flag=True,
              help='print literally, no pretty table')
@click.option('--filter', default=None)
@click.pass_context
def nsi_show1(ctx, name, literal, filter):
    """shows the content of a Network Slice Instance (NSI)

    NAME: name or ID of the Network Slice Instance
    """
    nsi_show(ctx, name, literal, filter)


@cli.command(name='netslice-instance-show', short_help='shows the content of a Network Slice Instance (NSI)')
@click.argument('name')
@click.option('--literal', is_flag=True,
              help='print literally, no pretty table')
@click.option('--filter', default=None)
@click.pass_context
def nsi_show2(ctx, name, literal, filter):
    """shows the content of a Network Slice Instance (NSI)

    NAME: name or ID of the Network Slice Instance
    """
    nsi_show(ctx, name, literal, filter)


def nsi_op_show(ctx, id, filter):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        op_info = ctx.obj.nsi.get_op(id)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    table = PrettyTable(['field', 'value'])
    for k, v in list(op_info.items()):
        if filter is None or filter in k:
            table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


@cli.command(name='nsi-op-show', short_help='shows the info of an operation over a Network Slice Instance(NSI)')
@click.argument('id')
@click.option('--filter', default=None)
@click.pass_context
def nsi_op_show1(ctx, id, filter):
    """shows the info of an operation over a Network Slice Instance(NSI)

    ID: operation identifier
    """
    nsi_op_show(ctx, id, filter)


@cli.command(name='netslice-instance-op-show', short_help='shows the info of an operation over a Network Slice Instance(NSI)')
@click.argument('id')
@click.option('--filter', default=None)
@click.pass_context
def nsi_op_show2(ctx, id, filter):
    """shows the info of an operation over a Network Slice Instance(NSI)

    ID: operation identifier
    """
    nsi_op_show(ctx, id, filter)


@cli.command(name='pdu-show', short_help='shows the content of a Physical Deployment Unit (PDU)')
@click.argument('name')
@click.option('--literal', is_flag=True,
              help='print literally, no pretty table')
@click.option('--filter', default=None)
@click.pass_context
def pdu_show(ctx, name, literal, filter):
    """shows the content of a Physical Deployment Unit (PDU)

    NAME: name or ID of the PDU
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        pdu = ctx.obj.pdu.get(name)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    if literal:
        print(yaml.safe_dump(pdu))
        return

    table = PrettyTable(['field', 'value'])

    for k, v in list(pdu.items()):
        if filter is None or filter in k:
            table.add_row([k, json.dumps(v, indent=2)])

    table.align = 'l'
    print(table)


####################
# CREATE operations
####################

def nsd_create(ctx, filename, overwrite):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.nsd.create(filename, overwrite)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='nsd-create', short_help='creates a new NSD/NSpkg')
@click.argument('filename')
@click.option('--overwrite', default=None,
              help='overwrites some fields in NSD')
@click.pass_context
def nsd_create1(ctx, filename, overwrite):
    """creates a new NSD/NSpkg

    FILENAME: NSD yaml file or NSpkg tar.gz file
    """
    nsd_create(ctx, filename, overwrite)


@cli.command(name='nspkg-create', short_help='creates a new NSD/NSpkg')
@click.argument('filename')
@click.option('--overwrite', default=None,
              help='overwrites some fields in NSD')
@click.pass_context
def nsd_create2(ctx, filename, overwrite):
    """creates a new NSD/NSpkg

    FILENAME: NSD yaml file or NSpkg tar.gz file
    """
    nsd_create(ctx, filename, overwrite)


def vnfd_create(ctx, filename, overwrite):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.vnfd.create(filename, overwrite)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='vnfd-create', short_help='creates a new VNFD/VNFpkg')
@click.argument('filename')
@click.option('--overwrite', default=None,
              help='overwrites some fields in VNFD')
@click.pass_context
def vnfd_create1(ctx, filename, overwrite):
    """creates a new VNFD/VNFpkg

    FILENAME: VNFD yaml file or VNFpkg tar.gz file
    """
    vnfd_create(ctx, filename, overwrite)


@cli.command(name='vnfpkg-create', short_help='creates a new VNFD/VNFpkg')
@click.argument('filename')
@click.option('--overwrite', default=None,
              help='overwrites some fields in VNFD')
@click.pass_context
def vnfd_create2(ctx, filename, overwrite):
    """creates a new VNFD/VNFpkg

    FILENAME: VNFD yaml file or VNFpkg tar.gz file
    """
    vnfd_create(ctx, filename, overwrite)


@cli.command(name='nfpkg-create', short_help='creates a new NFpkg')
@click.argument('filename')
@click.option('--overwrite', default=None,
              help='overwrites some fields in NFD')
@click.pass_context
def nfpkg_create(ctx, filename, overwrite):
    """creates a new NFpkg

    FILENAME: NF Descriptor yaml file or NFpkg tar.gz file
    """
    vnfd_create(ctx, filename, overwrite)


@cli.command(name='ns-create', short_help='creates a new Network Service instance')
@click.option('--ns_name',
              prompt=True, help='name of the NS instance')
@click.option('--nsd_name',
              prompt=True, help='name of the NS descriptor')
@click.option('--vim_account',
              prompt=True, help='default VIM account id or name for the deployment')
@click.option('--admin_status',
              default='ENABLED',
              help='administration status')
@click.option('--ssh_keys',
              default=None,
              help='comma separated list of public key files to inject to vnfs')
@click.option('--config',
              default=None,
              help='ns specific yaml configuration')
@click.option('--config_file',
              default=None,
              help='ns specific yaml configuration file')
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def ns_create(ctx,
              nsd_name,
              ns_name,
              vim_account,
              admin_status,
              ssh_keys,
              config,
              config_file,
              wait):
    """creates a new NS instance"""
    try:
        if config_file:
            check_client_version(ctx.obj, '--config_file')
            if config:
                raise ClientException('"--config" option is incompatible with "--config_file" option')
            with open(config_file, 'r') as cf:
                config=cf.read()
        ctx.obj.ns.create(
            nsd_name,
            ns_name,
            config=config,
            ssh_keys=ssh_keys,
            account=vim_account,
            wait=wait)
    except ClientException as inst:
        print(inst.message)
        exit(1)


def nst_create(ctx, filename, overwrite):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.nst.create(filename, overwrite)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='nst-create', short_help='creates a new Network Slice Template (NST)')
@click.argument('filename')
@click.option('--overwrite', default=None,
              help='overwrites some fields in NST')
@click.pass_context
def nst_create1(ctx, filename, overwrite):
    """creates a new Network Slice Template (NST)

    FILENAME: NST yaml file or NSTpkg tar.gz file
    """
    nst_create(ctx, filename, overwrite)


@cli.command(name='netslice-template-create', short_help='creates a new Network Slice Template (NST)')
@click.argument('filename')
@click.option('--overwrite', default=None,
              help='overwrites some fields in NST')
@click.pass_context
def nst_create2(ctx, filename, overwrite):
    """creates a new Network Slice Template (NST)

    FILENAME: NST yaml file or NSTpkg tar.gz file
    """
    nst_create(ctx, filename, overwrite)


def nsi_create(ctx, nst_name, nsi_name, vim_account, ssh_keys, config, config_file, wait):
    """creates a new Network Slice Instance (NSI)"""
    try:
        check_client_version(ctx.obj, ctx.command.name)
        if config_file:
            if config:
                raise ClientException('"--config" option is incompatible with "--config_file" option')
            with open(config_file, 'r') as cf:
                config=cf.read()
        ctx.obj.nsi.create(nst_name, nsi_name, config=config, ssh_keys=ssh_keys,
                           account=vim_account, wait=wait)
    except ClientException as inst:
        print(inst.message)
        exit(1)


@cli.command(name='nsi-create', short_help='creates a new Network Slice Instance')
@click.option('--nsi_name', prompt=True, help='name of the Network Slice Instance')
@click.option('--nst_name', prompt=True, help='name of the Network Slice Template')
@click.option('--vim_account', prompt=True, help='default VIM account id or name for the deployment')
@click.option('--ssh_keys', default=None,
              help='comma separated list of keys to inject to vnfs')
@click.option('--config', default=None,
              help='Netslice specific yaml configuration:\n'
              'netslice_subnet: [\n'
                'id: TEXT, vim_account: TEXT,\n'
                'vnf: [member-vnf-index: TEXT, vim_account: TEXT]\n'
                'vld: [name: TEXT, vim-network-name: TEXT or DICT with vim_account, vim_net entries]\n'
                'additionalParamsForNsi: {param: value, ...}\n'
                'additionalParamsForsubnet: [{id: SUBNET_ID, additionalParamsForNs: {}, additionalParamsForVnf: {}}]\n'
              '],\n'
              'netslice-vld: [name: TEXT, vim-network-name: TEXT or DICT with vim_account, vim_net entries]'
              )
@click.option('--config_file',
              default=None,
              help='nsi specific yaml configuration file')
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def nsi_create1(ctx, nst_name, nsi_name, vim_account, ssh_keys, config, config_file, wait):
    """creates a new Network Slice Instance (NSI)"""
    nsi_create(ctx, nst_name, nsi_name, vim_account, ssh_keys, config, config_file, wait=wait)


@cli.command(name='netslice-instance-create', short_help='creates a new Network Slice Instance')
@click.option('--nsi_name', prompt=True, help='name of the Network Slice Instance')
@click.option('--nst_name', prompt=True, help='name of the Network Slice Template')
@click.option('--vim_account', prompt=True, help='default VIM account id or name for the deployment')
@click.option('--ssh_keys', default=None,
              help='comma separated list of keys to inject to vnfs')
@click.option('--config', default=None,
              help='Netslice specific yaml configuration:\n'
              'netslice_subnet: [\n'
                'id: TEXT, vim_account: TEXT,\n'
                'vnf: [member-vnf-index: TEXT, vim_account: TEXT]\n'
                'vld: [name: TEXT, vim-network-name: TEXT or DICT with vim_account, vim_net entries]'
              '],\n'
              'netslice-vld: [name: TEXT, vim-network-name: TEXT or DICT with vim_account, vim_net entries]'
              )
@click.option('--config_file',
              default=None,
              help='nsi specific yaml configuration file')
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def nsi_create2(ctx, nst_name, nsi_name, vim_account, ssh_keys, config, config_file, wait):
    """creates a new Network Slice Instance (NSI)"""
    nsi_create(ctx, nst_name, nsi_name, vim_account, ssh_keys, config, config_file, wait=wait)


@cli.command(name='pdu-create', short_help='adds a new Physical Deployment Unit to the catalog')
@click.option('--name', help='name of the Physical Deployment Unit')
@click.option('--pdu_type', help='type of PDU (e.g. router, firewall, FW001)')
@click.option('--interface',
              help='interface(s) of the PDU: name=<NAME>,mgmt=<true|false>,ip-address=<IP_ADDRESS>'+
                   '[,type=<overlay|underlay>][,mac-address=<MAC_ADDRESS>][,vim-network-name=<VIM_NET_NAME>]',
              multiple=True)
@click.option('--description', help='human readable description')
@click.option('--vim_account', help='list of VIM accounts (in the same VIM) that can reach this PDU', multiple=True)
@click.option('--descriptor_file', default=None, help='PDU descriptor file (as an alternative to using the other arguments')
@click.pass_context
def pdu_create(ctx, name, pdu_type, interface, description, vim_account, descriptor_file):
    """creates a new Physical Deployment Unit (PDU)"""
    try:
        check_client_version(ctx.obj, ctx.command.name)
        pdu = {}
        if not descriptor_file:
            if not name:
                raise ClientException('in absence of descriptor file, option "--name" is mandatory')
            if not pdu_type:
                raise ClientException('in absence of descriptor file, option "--pdu_type" is mandatory')
            if not interface:
                raise ClientException('in absence of descriptor file, option "--interface" is mandatory (at least once)')
            if not vim_account:
                raise ClientException('in absence of descriptor file, option "--vim_account" is mandatory (at least once)')
        else:
            with open(descriptor_file, 'r') as df:
                pdu = yaml.load(df.read())
        if name: pdu["name"] = name
        if pdu_type: pdu["type"] = pdu_type
        if description: pdu["description"] = description
        if vim_account: pdu["vim_accounts"] = vim_account
        if interface:
            ifaces_list = []
            for iface in interface:
                new_iface={k:v for k,v in [i.split('=') for i in iface.split(',')]}
                new_iface["mgmt"] = (new_iface.get("mgmt","false").lower() == "true")
                ifaces_list.append(new_iface)
            pdu["interfaces"] = ifaces_list
        ctx.obj.pdu.create(pdu)
    except ClientException as inst:
        print((inst.message))
        exit(1)

####################
# UPDATE operations
####################

def nsd_update(ctx, name, content):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.nsd.update(name, content)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='nsd-update', short_help='updates a NSD/NSpkg')
@click.argument('name')
@click.option('--content', default=None,
              help='filename with the NSD/NSpkg replacing the current one')
@click.pass_context
def nsd_update1(ctx, name, content):
    """updates a NSD/NSpkg

    NAME: name or ID of the NSD/NSpkg
    """
    nsd_update(ctx, name, content)


@cli.command(name='nspkg-update', short_help='updates a NSD/NSpkg')
@click.argument('name')
@click.option('--content', default=None,
              help='filename with the NSD/NSpkg replacing the current one')
@click.pass_context
def nsd_update2(ctx, name, content):
    """updates a NSD/NSpkg

    NAME: name or ID of the NSD/NSpkg
    """
    nsd_update(ctx, name, content)


def vnfd_update(ctx, name, content):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.vnfd.update(name, content)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='vnfd-update', short_help='updates a new VNFD/VNFpkg')
@click.argument('name')
@click.option('--content', default=None,
              help='filename with the VNFD/VNFpkg replacing the current one')
@click.pass_context
def vnfd_update1(ctx, name, content):
    """updates a VNFD/VNFpkg

    NAME: name or ID of the VNFD/VNFpkg
    """
    vnfd_update(ctx, name, content)


@cli.command(name='vnfpkg-update', short_help='updates a VNFD/VNFpkg')
@click.argument('name')
@click.option('--content', default=None,
              help='filename with the VNFD/VNFpkg replacing the current one')
@click.pass_context
def vnfd_update2(ctx, name, content):
    """updates a VNFD/VNFpkg

    NAME: VNFD yaml file or VNFpkg tar.gz file
    """
    vnfd_update(ctx, name, content)


@cli.command(name='nfpkg-update', short_help='updates a NFpkg')
@click.argument('name')
@click.option('--content', default=None,
              help='filename with the NFpkg replacing the current one')
@click.pass_context
def nfpkg_update(ctx, name, content):
    """updates a NFpkg

    NAME: NF Descriptor yaml file or NFpkg tar.gz file
    """
    vnfd_update(ctx, name, content)


def nst_update(ctx, name, content):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.nst.update(name, content)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='nst-update', short_help='updates a Network Slice Template (NST)')
@click.argument('name')
@click.option('--content', default=None,
              help='filename with the NST/NSTpkg replacing the current one')
@click.pass_context
def nst_update1(ctx, name, content):
    """updates a Network Slice Template (NST)

    NAME: name or ID of the NSD/NSpkg
    """
    nst_update(ctx, name, content)


@cli.command(name='netslice-template-update', short_help='updates a Network Slice Template (NST)')
@click.argument('name')
@click.option('--content', default=None,
              help='filename with the NST/NSTpkg replacing the current one')
@click.pass_context
def nst_update2(ctx, name, content):
    """updates a Network Slice Template (NST)

    NAME: name or ID of the NSD/NSpkg
    """
    nst_update(ctx, name, content)


####################
# DELETE operations
####################

def nsd_delete(ctx, name, force):
    try:
        if not force:
            ctx.obj.nsd.delete(name)
        else:
            check_client_version(ctx.obj, '--force')
            ctx.obj.nsd.delete(name, force)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='nsd-delete', short_help='deletes a NSD/NSpkg')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.pass_context
def nsd_delete1(ctx, name, force):
    """deletes a NSD/NSpkg

    NAME: name or ID of the NSD/NSpkg to be deleted
    """
    nsd_delete(ctx, name, force)


@cli.command(name='nspkg-delete', short_help='deletes a NSD/NSpkg')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.pass_context
def nsd_delete2(ctx, name, force):
    """deletes a NSD/NSpkg

    NAME: name or ID of the NSD/NSpkg to be deleted
    """
    nsd_delete(ctx, name, force)


def vnfd_delete(ctx, name, force):
    try:
        if not force:
            ctx.obj.vnfd.delete(name)
        else:
            check_client_version(ctx.obj, '--force')
            ctx.obj.vnfd.delete(name, force)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='vnfd-delete', short_help='deletes a VNFD/VNFpkg')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.pass_context
def vnfd_delete1(ctx, name, force):
    """deletes a VNFD/VNFpkg

    NAME: name or ID of the VNFD/VNFpkg to be deleted
    """
    vnfd_delete(ctx, name, force)


@cli.command(name='vnfpkg-delete', short_help='deletes a VNFD/VNFpkg')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.pass_context
def vnfd_delete2(ctx, name, force):
    """deletes a VNFD/VNFpkg

    NAME: name or ID of the VNFD/VNFpkg to be deleted
    """
    vnfd_delete(ctx, name, force)


@cli.command(name='nfpkg-delete', short_help='deletes a NFpkg')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.pass_context
def nfpkg_delete(ctx, name, force):
    """deletes a NFpkg

    NAME: name or ID of the NFpkg to be deleted
    """
    vnfd_delete(ctx, name, force)


@cli.command(name='ns-delete', short_help='deletes a NS instance')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def ns_delete(ctx, name, force, wait):
    """deletes a NS instance

    NAME: name or ID of the NS instance to be deleted
    """
    try:
        if not force:
            ctx.obj.ns.delete(name, wait=wait)
        else:
            check_client_version(ctx.obj, '--force')
            ctx.obj.ns.delete(name, force, wait=wait)
    except ClientException as inst:
        print((inst.message))
        exit(1)


def nst_delete(ctx, name, force):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.nst.delete(name, force)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='nst-delete', short_help='deletes a Network Slice Template (NST)')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.pass_context
def nst_delete1(ctx, name, force):
    """deletes a Network Slice Template (NST)

    NAME: name or ID of the NST/NSTpkg to be deleted
    """
    nst_delete(ctx, name, force)


@cli.command(name='netslice-template-delete', short_help='deletes a Network Slice Template (NST)')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.pass_context
def nst_delete2(ctx, name, force):
    """deletes a Network Slice Template (NST)

    NAME: name or ID of the NST/NSTpkg to be deleted
    """
    nst_delete(ctx, name, force)


def nsi_delete(ctx, name, force, wait):
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.nsi.delete(name, force, wait=wait)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='nsi-delete', short_help='deletes a Network Slice Instance (NSI)')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def nsi_delete1(ctx, name, force, wait):
    """deletes a Network Slice Instance (NSI)

    NAME: name or ID of the Network Slice instance to be deleted
    """
    nsi_delete(ctx, name, force, wait=wait)


@cli.command(name='netslice-instance-delete', short_help='deletes a Network Slice Instance (NSI)')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.pass_context
def nsi_delete2(ctx, name, force, wait):
    """deletes a Network Slice Instance (NSI)

    NAME: name or ID of the Network Slice instance to be deleted
    """
    nsi_delete(ctx, name, force, wait=wait)


@cli.command(name='pdu-delete', short_help='deletes a Physical Deployment Unit (PDU)')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.pass_context
def pdu_delete(ctx, name, force):
    """deletes a Physical Deployment Unit (PDU)

    NAME: name or ID of the PDU to be deleted
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.pdu.delete(name, force)
    except ClientException as inst:
        print((inst.message))
        exit(1)


#################
# VIM operations
#################

@cli.command(name='vim-create')
@click.option('--name',
              prompt=True,
              help='Name to create datacenter')
@click.option('--user',
              prompt=True,
              help='VIM username')
@click.option('--password',
              prompt=True,
              hide_input=True,
              confirmation_prompt=True,
              help='VIM password')
@click.option('--auth_url',
              prompt=True,
              help='VIM url')
@click.option('--tenant',
              prompt=True,
              help='VIM tenant name')
@click.option('--config',
              default=None,
              help='VIM specific config parameters')
@click.option('--account_type',
              default='openstack',
              help='VIM type')
@click.option('--description',
              default='no description',
              help='human readable description')
@click.option('--sdn_controller', default=None, help='Name or id of the SDN controller associated to this VIM account')
@click.option('--sdn_port_mapping', default=None, help="File describing the port mapping between compute nodes' ports and switch ports")
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def vim_create(ctx,
               name,
               user,
               password,
               auth_url,
               tenant,
               config,
               account_type,
               description,
               sdn_controller,
               sdn_port_mapping,
               wait):
    """creates a new VIM account"""
    try:
        if sdn_controller:
            check_client_version(ctx.obj, '--sdn_controller')
        if sdn_port_mapping:
            check_client_version(ctx.obj, '--sdn_port_mapping')
        vim = {}
        vim['vim-username'] = user
        vim['vim-password'] = password
        vim['vim-url'] = auth_url
        vim['vim-tenant-name'] = tenant
        vim['vim-type'] = account_type
        vim['description'] = description
        vim['config'] = config
        if sdn_controller or sdn_port_mapping:
            ctx.obj.vim.create(name, vim, sdn_controller, sdn_port_mapping, wait=wait)
        else:
            ctx.obj.vim.create(name, vim, wait=wait)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='vim-update', short_help='updates a VIM account')
@click.argument('name')
@click.option('--newname', help='New name for the VIM account')
@click.option('--user', help='VIM username')
@click.option('--password', help='VIM password')
@click.option('--auth_url', help='VIM url')
@click.option('--tenant', help='VIM tenant name')
@click.option('--config', help='VIM specific config parameters')
@click.option('--account_type', help='VIM type')
@click.option('--description', help='human readable description')
@click.option('--sdn_controller', default=None, help='Name or id of the SDN controller associated to this VIM account')
@click.option('--sdn_port_mapping', default=None, help="File describing the port mapping between compute nodes' ports and switch ports")
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def vim_update(ctx,
               name,
               newname,
               user,
               password,
               auth_url,
               tenant,
               config,
               account_type,
               description,
               sdn_controller,
               sdn_port_mapping,
               wait):
    """updates a VIM account

    NAME: name or ID of the VIM account
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        vim = {}
        if newname: vim['name'] = newname
        if user: vim['vim_user'] = user
        if password: vim['vim_password'] = password
        if auth_url: vim['vim_url'] = auth_url
        if tenant: vim['vim-tenant-name'] = tenant
        if account_type: vim['vim_type'] = account_type
        if description: vim['description'] = description
        if config: vim['config'] = config
        ctx.obj.vim.update(name, vim, sdn_controller, sdn_port_mapping, wait=wait)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='vim-delete')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def vim_delete(ctx, name, force, wait):
    """deletes a VIM account

    NAME: name or ID of the VIM account to be deleted
    """
    try:
        if not force:
            ctx.obj.vim.delete(name, wait=wait)
        else:
            check_client_version(ctx.obj, '--force')
            ctx.obj.vim.delete(name, force, wait=wait)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='vim-list')
@click.option('--ro_update/--no_ro_update',
              default=False,
              help='update list from RO')
@click.option('--filter', default=None,
              help='restricts the list to the VIM accounts matching the filter')
@click.pass_context
def vim_list(ctx, ro_update, filter):
    """list all VIM accounts"""
    if filter:
        check_client_version(ctx.obj, '--filter')
    if ro_update:
        check_client_version(ctx.obj, '--ro_update', 'v1')
    fullclassname = ctx.obj.__module__ + "." + ctx.obj.__class__.__name__
    if fullclassname == 'osmclient.sol005.client.Client':
        resp = ctx.obj.vim.list(filter)
    else:
        resp = ctx.obj.vim.list(ro_update)
    table = PrettyTable(['vim name', 'uuid'])
    for vim in resp:
        table.add_row([vim['name'], vim['uuid']])
    table.align = 'l'
    print(table)


@cli.command(name='vim-show')
@click.argument('name')
@click.pass_context
def vim_show(ctx, name):
    """shows the details of a VIM account

    NAME: name or ID of the VIM account
    """
    try:
        resp = ctx.obj.vim.get(name)
        if 'vim_password' in resp:
            resp['vim_password']='********'
    except ClientException as inst:
        print((inst.message))
        exit(1)

    table = PrettyTable(['key', 'attribute'])
    for k, v in list(resp.items()):
        table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


####################
# WIM operations
####################

@cli.command(name='wim-create')
@click.option('--name',
              prompt=True,
              help='Name for the WIM account')
@click.option('--user',
              help='WIM username')
@click.option('--password',
              help='WIM password')
@click.option('--url',
              prompt=True,
              help='WIM url')
# @click.option('--tenant',
#               help='wIM tenant name')
@click.option('--config',
              default=None,
              help='WIM specific config parameters')
@click.option('--wim_type',
              help='WIM type')
@click.option('--description',
              default='no description',
              help='human readable description')
@click.option('--wim_port_mapping', default=None, help="File describing the port mapping between DC edge (datacenters, switches, ports) and WAN edge (WAN service endpoint id and info)")
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def wim_create(ctx,
               name,
               user,
               password,
               url,
               # tenant,
               config,
               wim_type,
               description,
               wim_port_mapping,
               wait):
    """creates a new WIM account"""
    try:
        check_client_version(ctx.obj, ctx.command.name)
        # if sdn_controller:
        #     check_client_version(ctx.obj, '--sdn_controller')
        # if sdn_port_mapping:
        #     check_client_version(ctx.obj, '--sdn_port_mapping')
        wim = {}
        if user: wim['user'] = user
        if password: wim['password'] = password
        if url: wim['wim_url'] = url
        # if tenant: wim['tenant'] = tenant
        wim['wim_type'] = wim_type
        if description: wim['description'] = description
        if config: wim['config'] = config
        ctx.obj.wim.create(name, wim, wim_port_mapping, wait=wait)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='wim-update', short_help='updates a WIM account')
@click.argument('name')
@click.option('--newname', help='New name for the WIM account')
@click.option('--user', help='WIM username')
@click.option('--password', help='WIM password')
@click.option('--url', help='WIM url')
@click.option('--config', help='WIM specific config parameters')
@click.option('--wim_type', help='WIM type')
@click.option('--description', help='human readable description')
@click.option('--wim_port_mapping', default=None, help="File describing the port mapping between DC edge (datacenters, switches, ports) and WAN edge (WAN service endpoint id and info)")
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def wim_update(ctx,
               name,
               newname,
               user,
               password,
               url,
               config,
               wim_type,
               description,
               wim_port_mapping,
               wait):
    """updates a WIM account

    NAME: name or ID of the WIM account
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        wim = {}
        if newname: wim['name'] = newname
        if user: wim['user'] = user
        if password: wim['password'] = password
        if url: wim['url'] = url
        # if tenant: wim['tenant'] = tenant
        if wim_type: wim['wim_type'] = wim_type
        if description: wim['description'] = description
        if config: wim['config'] = config
        ctx.obj.wim.update(name, wim, wim_port_mapping, wait=wait)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='wim-delete')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def wim_delete(ctx, name, force, wait):
    """deletes a WIM account

    NAME: name or ID of the WIM account to be deleted
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.wim.delete(name, force, wait=wait)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='wim-list')
@click.option('--filter', default=None,
              help='restricts the list to the WIM accounts matching the filter')
@click.pass_context
def wim_list(ctx, filter):
    """list all WIM accounts"""
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.wim.list(filter)
        table = PrettyTable(['wim name', 'uuid'])
        for wim in resp:
            table.add_row([wim['name'], wim['uuid']])
        table.align = 'l'
        print(table)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='wim-show')
@click.argument('name')
@click.pass_context
def wim_show(ctx, name):
    """shows the details of a WIM account

    NAME: name or ID of the WIM account
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.wim.get(name)
        if 'password' in resp:
            resp['wim_password']='********'
    except ClientException as inst:
        print((inst.message))
        exit(1)

    table = PrettyTable(['key', 'attribute'])
    for k, v in list(resp.items()):
        table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


####################
# SDN controller operations
####################

@cli.command(name='sdnc-create')
@click.option('--name',
              prompt=True,
              help='Name to create sdn controller')
@click.option('--type',
              prompt=True,
              help='SDN controller type')
@click.option('--sdn_controller_version',
              help='SDN controller version')
@click.option('--ip_address',
              prompt=True,
              help='SDN controller IP address')
@click.option('--port',
              prompt=True,
              help='SDN controller port')
@click.option('--switch_dpid',
              prompt=True,
              help='Switch DPID (Openflow Datapath ID)')
@click.option('--user',
              help='SDN controller username')
@click.option('--password',
              hide_input=True,
              confirmation_prompt=True,
              help='SDN controller password')
#@click.option('--description',
#              default='no description',
#              help='human readable description')
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def sdnc_create(ctx,
                name,
                type,
                sdn_controller_version,
                ip_address,
                port,
                switch_dpid,
                user,
                password,
                wait):
    """creates a new SDN controller"""
    sdncontroller = {}
    sdncontroller['name'] = name
    sdncontroller['type'] = type
    sdncontroller['ip'] = ip_address
    sdncontroller['port'] = int(port)
    sdncontroller['dpid'] = switch_dpid
    if sdn_controller_version:
        sdncontroller['version'] = sdn_controller_version
    if user:
        sdncontroller['user'] = user
    if password:
        sdncontroller['password'] = password
#    sdncontroller['description'] = description
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.sdnc.create(name, sdncontroller, wait=wait)
    except ClientException as inst:
        print((inst.message))
        exit(1)

@cli.command(name='sdnc-update', short_help='updates an SDN controller')
@click.argument('name')
@click.option('--newname', help='New name for the SDN controller')
@click.option('--type', help='SDN controller type')
@click.option('--sdn_controller_version', help='SDN controller username')
@click.option('--ip_address', help='SDN controller IP address')
@click.option('--port', help='SDN controller port')
@click.option('--switch_dpid', help='Switch DPID (Openflow Datapath ID)')
@click.option('--user', help='SDN controller username')
@click.option('--password', help='SDN controller password')
#@click.option('--description',  default=None, help='human readable description')
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def sdnc_update(ctx,
                name,
                newname,
                type,
                sdn_controller_version,
                ip_address,
                port,
                switch_dpid,
                user,
                password,
                wait):
    """updates an SDN controller

    NAME: name or ID of the SDN controller
    """
    sdncontroller = {}
    if newname: sdncontroller['name'] = newname
    if type: sdncontroller['type'] = type
    if ip_address: sdncontroller['ip'] = ip_address
    if port: sdncontroller['port'] = int(port)
    if switch_dpid: sdncontroller['dpid'] = switch_dpid
#    sdncontroller['description'] = description
    if sdn_controller_version is not None:
        if sdn_controller_version=="":
            sdncontroller['version'] = None
        else:
            sdncontroller['version'] = sdn_controller_version
    if user is not None:
        if user=="":
            sdncontroller['user'] = None
        else:
            sdncontroller['user'] = user
    if password is not None:
        if password=="":
            sdncontroller['password'] = None
        else:
            sdncontroller['password'] = user
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.sdnc.update(name, sdncontroller, wait=wait)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='sdnc-delete')
@click.argument('name')
@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def sdnc_delete(ctx, name, force, wait):
    """deletes an SDN controller

    NAME: name or ID of the SDN controller to be deleted
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.sdnc.delete(name, force, wait=wait)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='sdnc-list')
@click.option('--filter', default=None,
              help='restricts the list to the SDN controllers matching the filter')
@click.pass_context
def sdnc_list(ctx, filter):
    """list all SDN controllers"""
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.sdnc.list(filter)
    except ClientException as inst:
        print((inst.message))
        exit(1)
    table = PrettyTable(['sdnc name', 'id'])
    for sdnc in resp:
        table.add_row([sdnc['name'], sdnc['_id']])
    table.align = 'l'
    print(table)


@cli.command(name='sdnc-show')
@click.argument('name')
@click.pass_context
def sdnc_show(ctx, name):
    """shows the details of an SDN controller

    NAME: name or ID of the SDN controller
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.sdnc.get(name)
    except ClientException as inst:
        print((inst.message))
        exit(1)

    table = PrettyTable(['key', 'attribute'])
    for k, v in list(resp.items()):
        table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


####################
# Project mgmt operations
####################

@cli.command(name='project-create')
@click.argument('name')
#@click.option('--description',
#              default='no description',
#              help='human readable description')
@click.pass_context
def project_create(ctx, name):
    """Creates a new project

    NAME: name of the project
    """
    project = {}
    project['name'] = name
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.project.create(name, project)
    except ClientException as inst:
        print(inst.message)
        exit(1)


@cli.command(name='project-delete')
@click.argument('name')
#@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.pass_context
def project_delete(ctx, name):
    """deletes a project

    NAME: name or ID of the project to be deleted
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.project.delete(name)
    except ClientException as inst:
        print(inst.message)
        exit(1)


@cli.command(name='project-list')
@click.option('--filter', default=None,
              help='restricts the list to the projects matching the filter')
@click.pass_context
def project_list(ctx, filter):
    """list all projects"""
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.project.list(filter)
    except ClientException as inst:
        print(inst.message)
        exit(1)
    table = PrettyTable(['name', 'id'])
    for proj in resp:
        table.add_row([proj['name'], proj['_id']])
    table.align = 'l'
    print(table)


@cli.command(name='project-show')
@click.argument('name')
@click.pass_context
def project_show(ctx, name):
    """shows the details of a project

    NAME: name or ID of the project
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.project.get(name)
    except ClientException as inst:
        print(inst.message)
        exit(1)

    table = PrettyTable(['key', 'attribute'])
    for k, v in resp.items():
        table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


@cli.command(name='project-update')
@click.argument('project')
@click.option('--name',
              prompt=True,
              help='new name for the project')

@click.pass_context
def project_update(ctx, project, name):
    """
    Update a project name

    :param ctx:
    :param project: id or name of the project to modify
    :param name:  new name for the project
    :return:
    """

    project_changes = {}
    project_changes['name'] = name

    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.project.update(project, project_changes)
    except ClientException as inst:
        print(inst.message)


####################
# User mgmt operations
####################

@cli.command(name='user-create')
@click.argument('username')
@click.option('--password',
              prompt=True,
              hide_input=True,
              confirmation_prompt=True,
              help='user password')
@click.option('--projects',
              # prompt="Comma separate list of projects",
              multiple=True,
              callback=lambda ctx, param, value: ''.join(value).split(',') if all(len(x)==1 for x in value) else value,
              help='list of project ids that the user belongs to')
@click.option('--project-role-mappings', 'project_role_mappings',
              default=None, multiple=True,
              help='creating user project/role(s) mapping')
@click.pass_context
def user_create(ctx, username, password, projects, project_role_mappings):
    """Creates a new user

    \b
    USERNAME: name of the user
    PASSWORD: password of the user
    PROJECTS: projects assigned to user (internal only)
    PROJECT_ROLE_MAPPING: roles in projects assigned to user (keystone)
    """
    user = {}
    user['username'] = username
    user['password'] = password
    user['projects'] = projects
    user['project_role_mappings'] = project_role_mappings
    
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.user.create(username, user)
    except ClientException as inst:
        print(inst.message)
        exit(1)


@cli.command(name='user-update')
@click.argument('username')
@click.option('--password',
              # prompt=True,
              # hide_input=True,
              # confirmation_prompt=True,
              help='user password')
@click.option('--set-username', 'set_username',
              default=None,
              help='change username')
@click.option('--set-project', 'set_project',
              default=None, multiple=True,
              help='create/replace the project,role(s) mapping for this project: \'project,role1,role2,...\'')
@click.option('--remove-project', 'remove_project',
              default=None, multiple=True,
              help='removes project from user: \'project\'')
@click.option('--add-project-role', 'add_project_role',
              default=None, multiple=True,
              help='adds project,role(s) mapping: \'project,role1,role2,...\'')
@click.option('--remove-project-role', 'remove_project_role',
              default=None, multiple=True,
              help='removes project,role(s) mapping: \'project,role1,role2,...\'')
@click.pass_context
def user_update(ctx, username, password, set_username, set_project, remove_project,
                add_project_role, remove_project_role):
    """Update a user information

    \b
    USERNAME: name of the user
    PASSWORD: new password
    SET_USERNAME: new username
    SET_PROJECT: creating mappings for project/role(s)
    REMOVE_PROJECT: deleting mappings for project/role(s)
    ADD_PROJECT_ROLE: adding mappings for project/role(s)
    REMOVE_PROJECT_ROLE: removing mappings for project/role(s)
    """
    user = {}
    user['password'] = password
    user['username'] = set_username
    user['set-project'] = set_project
    user['remove-project'] = remove_project
    user['add-project-role'] = add_project_role
    user['remove-project-role'] = remove_project_role
    
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.user.update(username, user)
    except ClientException as inst:
        print(inst.message)
        exit(1)


@cli.command(name='user-delete')
@click.argument('name')
#@click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.pass_context
def user_delete(ctx, name):
    """deletes a user

    \b
    NAME: name or ID of the user to be deleted
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.user.delete(name)
    except ClientException as inst:
        print(inst.message)
        exit(1)


@cli.command(name='user-list')
@click.option('--filter', default=None,
              help='restricts the list to the users matching the filter')
@click.pass_context
def user_list(ctx, filter):
    """list all users"""
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.user.list(filter)
    except ClientException as inst:
        print(inst.message)
        exit(1)
    table = PrettyTable(['name', 'id'])
    for user in resp:
        table.add_row([user['username'], user['_id']])
    table.align = 'l'
    print(table)


@cli.command(name='user-show')
@click.argument('name')
@click.pass_context
def user_show(ctx, name):
    """shows the details of a user

    NAME: name or ID of the user
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.user.get(name)
        if 'password' in resp:
            resp['password']='********'
    except ClientException as inst:
        print(inst.message)
        exit(1)

    table = PrettyTable(['key', 'attribute'])
    for k, v in resp.items():
        table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


####################
# Fault Management operations
####################

@cli.command(name='ns-alarm-create')
@click.argument('name')
@click.option('--ns', prompt=True, help='NS instance id or name')
@click.option('--vnf', prompt=True,
              help='VNF name (VNF member index as declared in the NSD)')
@click.option('--vdu', prompt=True,
              help='VDU name (VDU name as declared in the VNFD)')
@click.option('--metric', prompt=True,
              help='Name of the metric (e.g. cpu_utilization)')
@click.option('--severity', default='WARNING',
              help='severity of the alarm (WARNING, MINOR, MAJOR, CRITICAL, INDETERMINATE)')
@click.option('--threshold_value', prompt=True,
              help='threshold value that, when crossed, an alarm is triggered')
@click.option('--threshold_operator', prompt=True,
              help='threshold operator describing the comparison (GE, LE, GT, LT, EQ)')
@click.option('--statistic', default='AVERAGE',
              help='statistic (AVERAGE, MINIMUM, MAXIMUM, COUNT, SUM)')
@click.pass_context
def ns_alarm_create(ctx, name, ns, vnf, vdu, metric, severity,
                    threshold_value, threshold_operator, statistic):
    """creates a new alarm for a NS instance"""
    # TODO: Check how to validate threshold_value.
    # Should it be an integer (1-100), percentage, or decimal (0.01-1.00)?
    try:
        ns_instance = ctx.obj.ns.get(ns)
        alarm = {}
        alarm['alarm_name'] = name
        alarm['ns_id'] = ns_instance['_id']
        alarm['correlation_id'] = ns_instance['_id']
        alarm['vnf_member_index'] = vnf
        alarm['vdu_name'] = vdu
        alarm['metric_name'] = metric
        alarm['severity'] = severity
        alarm['threshold_value'] = int(threshold_value)
        alarm['operation'] = threshold_operator
        alarm['statistic'] = statistic
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.ns.create_alarm(alarm)
    except ClientException as inst:
        print((inst.message))
        exit(1)


#@cli.command(name='ns-alarm-delete')
#@click.argument('name')
#@click.pass_context
#def ns_alarm_delete(ctx, name):
#    """deletes an alarm
#
#    NAME: name of the alarm to be deleted
#    """
#    try:
#        check_client_version(ctx.obj, ctx.command.name)
#        ctx.obj.ns.delete_alarm(name)
#    except ClientException as inst:
#        print(inst.message)
#        exit(1)


####################
# Performance Management operations
####################

@cli.command(name='ns-metric-export')
@click.option('--ns', prompt=True, help='NS instance id or name')
@click.option('--vnf', prompt=True,
              help='VNF name (VNF member index as declared in the NSD)')
@click.option('--vdu', prompt=True,
              help='VDU name (VDU name as declared in the VNFD)')
@click.option('--metric', prompt=True,
              help='name of the metric (e.g. cpu_utilization)')
#@click.option('--period', default='1w',
#              help='metric collection period (e.g. 20s, 30m, 2h, 3d, 1w)')
@click.option('--interval', help='periodic interval (seconds) to export metrics continuously')
@click.pass_context
def ns_metric_export(ctx, ns, vnf, vdu, metric, interval):
    """exports a metric to the internal OSM bus, which can be read by other apps"""
    # TODO: Check how to validate interval.
    # Should it be an integer (seconds), or should a suffix (s,m,h,d,w) also be permitted?
    try:
        ns_instance = ctx.obj.ns.get(ns)
        metric_data = {}
        metric_data['ns_id'] = ns_instance['_id']
        metric_data['correlation_id'] = ns_instance['_id']
        metric_data['vnf_member_index'] = vnf
        metric_data['vdu_name'] = vdu
        metric_data['metric_name'] = metric
        metric_data['collection_unit'] = 'WEEK'
        metric_data['collection_period'] = 1
        check_client_version(ctx.obj, ctx.command.name)
        if not interval:
            print('{}'.format(ctx.obj.ns.export_metric(metric_data)))
        else:
            i = 1
            while True:
                print('{} {}'.format(ctx.obj.ns.export_metric(metric_data),i))
                time.sleep(int(interval))
                i+=1
    except ClientException as inst:
        print((inst.message))
        exit(1)


####################
# Other operations
####################

@cli.command(name='upload-package')
@click.argument('filename')
@click.pass_context
def upload_package(ctx, filename):
    """uploads a VNF package or NS package

    FILENAME: VNF or NS package file (tar.gz)
    """
    try:
        ctx.obj.package.upload(filename)
        fullclassname = ctx.obj.__module__ + "." + ctx.obj.__class__.__name__
        if fullclassname != 'osmclient.sol005.client.Client':
            ctx.obj.package.wait_for_upload(filename)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='ns-scaling-show')
@click.argument('ns_name')
@click.pass_context
def show_ns_scaling(ctx, ns_name):
    """shows the status of a NS scaling operation

    NS_NAME: name of the NS instance being scaled
    """
    try:
        check_client_version(ctx.obj, ctx.command.name, 'v1')
        resp = ctx.obj.ns.list()
    except ClientException as inst:
        print((inst.message))
        exit(1)

    table = PrettyTable(
        ['group-name',
         'instance-id',
         'operational status',
         'create-time',
         'vnfr ids'])

    for ns in resp:
        if ns_name == ns['name']:
            nsopdata = ctx.obj.ns.get_opdata(ns['id'])
            scaling_records = nsopdata['nsr:nsr']['scaling-group-record']
            for record in scaling_records:
                if 'instance' in record:
                    instances = record['instance']
                    for inst in instances:
                        table.add_row(
                            [record['scaling-group-name-ref'],
                             inst['instance-id'],
                                inst['op-status'],
                                time.strftime('%Y-%m-%d %H:%M:%S',
                                              time.localtime(
                                                  inst['create-time'])),
                                inst['vnfrs']])
    table.align = 'l'
    print(table)


@cli.command(name='ns-scale')
@click.argument('ns_name')
@click.option('--ns_scale_group', prompt=True)
@click.option('--index', prompt=True)
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def ns_scale(ctx, ns_name, ns_scale_group, index, wait):
    """scales NS

    NS_NAME: name of the NS instance to be scaled
    """
    try:
        check_client_version(ctx.obj, ctx.command.name, 'v1')
        ctx.obj.ns.scale(ns_name, ns_scale_group, index, wait=wait)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='config-agent-list')
@click.pass_context
def config_agent_list(ctx):
    """list config agents"""
    try:
        check_client_version(ctx.obj, ctx.command.name, 'v1')
    except ClientException as inst:
        print((inst.message))
        exit(1)
    table = PrettyTable(['name', 'account-type', 'details'])
    for account in ctx.obj.vca.list():
        table.add_row(
            [account['name'],
             account['account-type'],
             account['juju']])
    table.align = 'l'
    print(table)


@cli.command(name='config-agent-delete')
@click.argument('name')
@click.pass_context
def config_agent_delete(ctx, name):
    """deletes a config agent

    NAME: name of the config agent to be deleted
    """
    try:
        check_client_version(ctx.obj, ctx.command.name, 'v1')
        ctx.obj.vca.delete(name)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='config-agent-add')
@click.option('--name',
              prompt=True)
@click.option('--account_type',
              prompt=True)
@click.option('--server',
              prompt=True)
@click.option('--user',
              prompt=True)
@click.option('--secret',
              prompt=True,
              hide_input=True,
              confirmation_prompt=True)
@click.pass_context
def config_agent_add(ctx, name, account_type, server, user, secret):
    """adds a config agent"""
    try:
        check_client_version(ctx.obj, ctx.command.name, 'v1')
        ctx.obj.vca.create(name, account_type, server, user, secret)
    except ClientException as inst:
        print((inst.message))
        exit(1)


@cli.command(name='ro-dump')
@click.pass_context
def ro_dump(ctx):
    """shows RO agent information"""
    check_client_version(ctx.obj, ctx.command.name, 'v1')
    resp = ctx.obj.vim.get_resource_orchestrator()
    table = PrettyTable(['key', 'attribute'])
    for k, v in list(resp.items()):
        table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


@cli.command(name='vcs-list')
@click.pass_context
def vcs_list(ctx):
    check_client_version(ctx.obj, ctx.command.name, 'v1')
    resp = ctx.obj.utils.get_vcs_info()
    table = PrettyTable(['component name', 'state'])
    for component in resp:
        table.add_row([component['component_name'], component['state']])
    table.align = 'l'
    print(table)


@cli.command(name='ns-action')
@click.argument('ns_name')
@click.option('--vnf_name', default=None, help='member-vnf-index if the target is a vnf instead of a ns)')
@click.option('--vdu_id', default=None, help='vdu-id if the target is a vdu o a vnf')
@click.option('--vdu_count', default=None, help='number of vdu instance of this vdu_id')
@click.option('--action_name', prompt=True)
@click.option('--params', default=None)
@click.option('--wait',
              required=False,
              default=False,
              is_flag=True,
              help='do not return the control immediately, but keep it \
              until the operation is completed, or timeout')
@click.pass_context
def ns_action(ctx,
              ns_name,
              vnf_name,
              vdu_id,
              vdu_count,
              action_name,
              params,
              wait):
    """executes an action/primitive over a NS instance

    NS_NAME: name or ID of the NS instance
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        op_data = {}
        if vnf_name:
            op_data['member_vnf_index'] = vnf_name
        if vdu_id:
            op_data['vdu_id'] = vdu_id
        if vdu_count:
            op_data['vdu_count_index'] = vdu_count
        op_data['primitive'] = action_name
        if params:
            op_data['primitive_params'] = yaml.load(params)
        else:
            op_data['primitive_params'] = {}
        ctx.obj.ns.exec_op(ns_name, op_name='action', op_data=op_data, wait=wait)

    except ClientException as inst:
        print(inst.message)
        exit(1)


@cli.command(name='vnf-scale')
@click.argument('ns_name')
@click.argument('vnf_name')
@click.option('--scaling-group', prompt=True, help="scaling-group-descriptor name to use")
@click.option('--scale-in', default=False, is_flag=True, help="performs a scale in operation")
@click.option('--scale-out', default=False, is_flag=True, help="performs a scale out operation (by default)")
@click.pass_context
def vnf_scale(ctx,
              ns_name,
              vnf_name,
              scaling_group,
              scale_in,
              scale_out):
    """
    Executes a VNF scale (adding/removing VDUs)

    \b
    NS_NAME: name or ID of the NS instance.
    VNF_NAME: member-vnf-index in the NS to be scaled.
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        if not scale_in and not scale_out:
            scale_out = True
        ctx.obj.ns.scale_vnf(ns_name, vnf_name, scaling_group, scale_in, scale_out)
    except ClientException as inst:
        print((inst.message))
        exit(1)


##############################
# Role Management Operations #
##############################

@cli.command(name='role-create', short_help='creates a role')
@click.argument('name')
@click.option('--permissions',
              default=None,
              help='role permissions using a dictionary')
@click.pass_context
def role_create(ctx, name, permissions):
    """
    Creates a new role.

    \b
    NAME: Name or ID of the role.
    DEFINITION: Definition of grant/denial of access to resources.
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.role.create(name, permissions)
    except ClientException as inst:
        print(inst.message)
        exit(1)


@cli.command(name='role-update', short_help='updates a role')
@click.argument('name')
@click.option('--set-name',
              default=None,
              help='change name of rle')
# @click.option('--permissions',
#               default=None,
#               help='provide a yaml format dictionary with incremental changes. Values can be bool or None to delete')
@click.option('--add',
              default=None,
              help='yaml format dictionary with permission: True/False to access grant/denial')
@click.option('--remove',
              default=None,
              help='yaml format list to remove a permission')
@click.pass_context
def role_update(ctx, name, set_name, add, remove):
    """
    Updates a role.

    \b
    NAME: Name or ID of the role.
    DEFINITION: Definition overwrites the old definition.
    ADD: Grant/denial of access to resource to add.
    REMOVE: Grant/denial of access to resource to remove.
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.role.update(name, set_name, None, add, remove)
    except ClientException as inst:
        print(inst.message)
        exit(1)


@cli.command(name='role-delete', short_help='deletes a role')
@click.argument('name')
# @click.option('--force', is_flag=True, help='forces the deletion bypassing pre-conditions')
@click.pass_context
def role_delete(ctx, name):
    """
    Deletes a role.

    \b
    NAME: Name or ID of the role.
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        ctx.obj.role.delete(name)
    except ClientException as inst:
        print(inst.message)
        exit(1)


@cli.command(name='role-list', short_help='list all roles')
@click.option('--filter', default=None,
              help='restricts the list to the projects matching the filter')
@click.pass_context
def role_list(ctx, filter):
    """
    List all roles.
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.role.list(filter)
    except ClientException as inst:
        print(inst.message)
        exit(1)
    table = PrettyTable(['name', 'id'])
    for role in resp:
        table.add_row([role['name'], role['_id']])
    table.align = 'l'
    print(table)


@cli.command(name='role-show', short_help='show specific role')
@click.argument('name')
@click.pass_context
def role_show(ctx, name):
    """
    Shows the details of a role.

    \b
    NAME: Name or ID of the role.
    """
    try:
        check_client_version(ctx.obj, ctx.command.name)
        resp = ctx.obj.role.get(name)
    except ClientException as inst:
        print(inst.message)
        exit(1)

    table = PrettyTable(['key', 'attribute'])
    for k, v in resp.items():
        table.add_row([k, json.dumps(v, indent=2)])
    table.align = 'l'
    print(table)


if __name__ == '__main__':
    try:
        cli()
    except pycurl.error as e:
        print(e)
        print('Maybe "--hostname" option or OSM_HOSTNAME' +
              'environment variable needs to be specified')
        exit(1)
