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
OSM NSI (Network Slice Instance) API handling
"""

from tngsdk.osmclient.common import utils
from tngsdk.osmclient.common import wait as WaitForStatus
from tngsdk.osmclient.common.exceptions import ClientException
from tngsdk.osmclient.common.exceptions import NotFound
import yaml
import json


class Nsi(object):

    def __init__(self, http=None, client=None):
        self._http = http
        self._client = client
        self._apiName = '/nsilcm'
        self._apiVersion = '/v1'
        self._apiResource = '/netslice_instances_content'
        self._apiBase = '{}{}{}'.format(self._apiName,
                                        self._apiVersion, self._apiResource)

    # NSI '--wait' option
    def _wait(self, id, deleteFlag=False):
        # Endpoint to get operation status
        apiUrlStatus = '{}{}{}'.format(self._apiName, self._apiVersion, '/nsi_lcm_op_occs')
        # Wait for status for NSI instance creation/update/deletion
        WaitForStatus.wait_for_status(
            'NSI',
            str(id),
            WaitForStatus.TIMEOUT_NSI_OPERATION,
            apiUrlStatus,
            self._http.get2_cmd,
            deleteFlag=deleteFlag)

    def list(self, filter=None):
        """Returns a list of NSI
        """
        filter_string = ''
        if filter:
            filter_string = '?{}'.format(filter)
        resp = self._http.get_cmd('{}{}'.format(self._apiBase,filter_string))
        if resp:
            return resp
        return list()

    def get(self, name):
        """Returns an NSI based on name or id
        """
        if utils.validate_uuid4(name):
            for nsi in self.list():
                if name == nsi['_id']:
                    return nsi
        else:
            for nsi in self.list():
                if name == nsi['name']:
                    return nsi
        raise NotFound("nsi {} not found".format(name))

    def get_individual(self, name):
        nsi_id = name
        if not utils.validate_uuid4(name):
            for nsi in self.list():
                if name == nsi['name']:
                    nsi_id = nsi['_id']
                    break
        resp = self._http.get_cmd('{}/{}'.format(self._apiBase, nsi_id))
        #resp = self._http.get_cmd('{}/{}/nsd_content'.format(self._apiBase, nsi_id))
        #print yaml.safe_dump(resp)
        if resp:
            return resp
        raise NotFound("nsi {} not found".format(name))

    def delete(self, name, force=False, wait=False):
        nsi = self.get(name)
        querystring = ''
        if force:
            querystring = '?FORCE=True'
        http_code, resp = self._http.delete_cmd('{}/{}{}'.format(self._apiBase,
                                         nsi['_id'], querystring))
        # print 'HTTP CODE: {}'.format(http_code)
        # print 'RESP: {}'.format(resp)
        if http_code == 202:
            if wait and resp:
                resp = json.loads(resp)
                # Wait for status for NSI instance deletion
                # For the 'delete' operation, '_id' is used
                self._wait(resp.get('_id'), deleteFlag=True)
            else:
                print('Deletion in progress')
        elif http_code == 204:
            print('Deleted')
        else:
            msg = ""
            if resp:
                try:
                    msg = json.loads(resp)
                except ValueError:
                    msg = resp
            raise ClientException("failed to delete nsi {} - {}".format(name, msg))

    def create(self, nst_name, nsi_name, account, config=None,
               ssh_keys=None, description='default description',
               admin_status='ENABLED', wait=False):

        nst = self._client.nst.get(nst_name)

        vim_account_id = {}

        def get_vim_account_id(vim_account):
            if vim_account_id.get(vim_account):
                return vim_account_id[vim_account]

            vim = self._client.vim.get(vim_account)
            if vim is None:
                raise NotFound("cannot find vim account '{}'".format(vim_account))
            vim_account_id[vim_account] = vim['_id']
            return vim['_id']

        nsi = {}
        nsi['nstId'] = nst['_id']
        nsi['nsiName'] = nsi_name
        nsi['nsiDescription'] = description
        nsi['vimAccountId'] = get_vim_account_id(account)
        #nsi['userdata'] = {}
        #nsi['userdata']['key1']='value1'
        #nsi['userdata']['key2']='value2'

        if ssh_keys is not None:
            # ssh_keys is comma separate list
            # ssh_keys_format = []
            # for key in ssh_keys.split(','):
            #     ssh_keys_format.append({'key-pair-ref': key})
            #
            # ns['ssh-authorized-key'] = ssh_keys_format
            nsi['ssh_keys'] = []
            for pubkeyfile in ssh_keys.split(','):
                with open(pubkeyfile, 'r') as f:
                    nsi['ssh_keys'].append(f.read())
        if config:
            nsi_config = yaml.load(config)
            if "netslice-vld" in nsi_config:
                for vld in nsi_config["netslice-vld"]:
                    if vld.get("vim-network-name"):
                        if isinstance(vld["vim-network-name"], dict):
                            vim_network_name_dict = {}
                            for vim_account, vim_net in list(vld["vim-network-name"].items()):
                                vim_network_name_dict[get_vim_account_id(vim_account)] = vim_net
                            vld["vim-network-name"] = vim_network_name_dict
                nsi["netslice-vld"] = nsi_config["netslice-vld"]
            if "netslice-subnet" in nsi_config:
                for nssubnet in nsi_config["netslice-subnet"]:
                    if "vld" in nssubnet:
                        for vld in nssubnet["vld"]:
                            if vld.get("vim-network-name"):
                                if isinstance(vld["vim-network-name"], dict):
                                    vim_network_name_dict = {}
                                    for vim_account, vim_net in list(vld["vim-network-name"].items()):
                                        vim_network_name_dict[get_vim_account_id(vim_account)] = vim_net
                                    vld["vim-network-name"] = vim_network_name_dict
                    if "vnf" in nssubnet:
                        for vnf in nsi_config["vnf"]:
                            if vnf.get("vim_account"):
                                vnf["vimAccountId"] = get_vim_account_id(vnf.pop("vim_account"))
                nsi["netslice-subnet"] = nsi_config["netslice-subnet"]

            if "additionalParamsForNsi" in nsi_config:
                nsi["additionalParamsForNsi"] = nsi_config.pop("additionalParamsForNsi")
                if not isinstance(nsi["additionalParamsForNsi"], dict):
                    raise ValueError("Error at --config 'additionalParamsForNsi' must be a dictionary")
            if "additionalParamsForSubnet" in nsi_config:
                nsi["additionalParamsForSubnet"] = nsi_config.pop("additionalParamsForSubnet")
                if not isinstance(nsi["additionalParamsForSubnet"], list):
                    raise ValueError("Error at --config 'additionalParamsForSubnet' must be a list")
                for additional_param_subnet in nsi["additionalParamsForSubnet"]:
                    if not isinstance(additional_param_subnet, dict):
                        raise ValueError("Error at --config 'additionalParamsForSubnet' items must be dictionaries")
                    if not additional_param_subnet.get("id"):
                        raise ValueError("Error at --config 'additionalParamsForSubnet' items must contain subnet 'id'")
                    if not additional_param_subnet.get("additionalParamsForNs") and\
                            not additional_param_subnet.get("additionalParamsForVnf"):
                        raise ValueError("Error at --config 'additionalParamsForSubnet' items must contain "
                                         "'additionalParamsForNs' and/or 'additionalParamsForVnf'")

        # print yaml.safe_dump(nsi)
        try:
            self._apiResource = '/netslice_instances_content'
            self._apiBase = '{}{}{}'.format(self._apiName,
                                            self._apiVersion, self._apiResource)
            headers = self._client._headers
            headers['Content-Type'] = 'application/yaml'
            http_header = ['{}: {}'.format(key,val)
                          for (key,val) in list(headers.items())]
            self._http.set_http_header(http_header)
            http_code, resp = self._http.post_cmd(endpoint=self._apiBase,
                                       postfields_dict=nsi)
            #print 'HTTP CODE: {}'.format(http_code)
            #print 'RESP: {}'.format(resp)
            if http_code in (200, 201, 202, 204):
                if resp:
                    resp = json.loads(resp)
                if not resp or 'id' not in resp:
                    raise ClientException('unexpected response from server - {} '.format(
                                      resp))
                if wait:
                    # Wait for status for NSI instance creation
                    self._wait(resp.get('nsilcmop_id'))
                print(resp['id'])
            else:
                msg = ""
                if resp:
                    try:
                        msg = json.loads(resp)
                    except ValueError:
                        msg = resp
                raise ClientException(msg)
        except ClientException as exc:
            message="failed to create nsi: {} nst: {}\nerror:\n{}".format(
                    nsi_name,
                    nst_name,
                    exc.message)
            raise ClientException(message)

    def list_op(self, name, filter=None):
        """Returns the list of operations of a NSI
        """
        nsi = self.get(name)
        try:
            self._apiResource = '/nsi_lcm_op_occs'
            self._apiBase = '{}{}{}'.format(self._apiName,
                                      self._apiVersion, self._apiResource)
            filter_string = ''
            if filter:
                filter_string = '&{}'.format(filter)
            http_code, resp = self._http.get2_cmd('{}?netsliceInstanceId={}'.format(
                                                       self._apiBase, nsi['_id'],
                                                       filter_string) )
            #print 'HTTP CODE: {}'.format(http_code)
            #print 'RESP: {}'.format(resp)
            if http_code == 200:
                if resp:
                    resp = json.loads(resp)
                    return resp
                else:
                    raise ClientException('unexpected response from server')
            else:
                msg = ""
                if resp:
                    try:
                        resp = json.loads(resp)
                        msg = resp['detail']
                    except ValueError:
                        msg = resp
                raise ClientException(msg)
        except ClientException as exc:
            message="failed to get operation list of NSI {}:\nerror:\n{}".format(
                    name,
                    exc.message)
            raise ClientException(message)

    def get_op(self, operationId):
        """Returns the status of an operation
        """
        try:
            self._apiResource = '/nsi_lcm_op_occs'
            self._apiBase = '{}{}{}'.format(self._apiName,
                                      self._apiVersion, self._apiResource)
            http_code, resp = self._http.get2_cmd('{}/{}'.format(self._apiBase, operationId))
            #print 'HTTP CODE: {}'.format(http_code)
            #print 'RESP: {}'.format(resp)
            if http_code == 200:
                if resp:
                    resp = json.loads(resp)
                    return resp
                else:
                    raise ClientException('unexpected response from server')
            else:
                msg = ""
                if resp:
                    try:
                        resp = json.loads(resp)
                        msg = resp['detail']
                    except ValueError:
                        msg = resp
                raise ClientException(msg)
        except ClientException as exc:
            message="failed to get status of operation {}:\nerror:\n{}".format(
                    operationId,
                    exc.message)
            raise ClientException(message)

    def exec_op(self, name, op_name, op_data=None):
        """Executes an operation on a NSI
        """
        nsi = self.get(name)
        try:
            self._apiResource = '/netslice_instances'
            self._apiBase = '{}{}{}'.format(self._apiName,
                                            self._apiVersion, self._apiResource)
            endpoint = '{}/{}/{}'.format(self._apiBase, nsi['_id'], op_name)
            #print 'OP_NAME: {}'.format(op_name)
            #print 'OP_DATA: {}'.format(json.dumps(op_data))
            http_code, resp = self._http.post_cmd(endpoint=endpoint, postfields_dict=op_data)
            #print 'HTTP CODE: {}'.format(http_code)
            #print 'RESP: {}'.format(resp)
            if http_code in (200, 201, 202, 204):
                if resp:
                    resp = json.loads(resp)
                if not resp or 'id' not in resp:
                    raise ClientException('unexpected response from server - {}'.format(
                                      resp))
                print(resp['id'])
            else:
                msg = ""
                if resp:
                    try:
                        msg = json.loads(resp)
                    except ValueError:
                        msg = resp
                raise ClientException(msg)
        except ClientException as exc:
            message="failed to exec operation {}:\nerror:\n{}".format(
                    name,
                    exc.message)
            raise ClientException(message)

