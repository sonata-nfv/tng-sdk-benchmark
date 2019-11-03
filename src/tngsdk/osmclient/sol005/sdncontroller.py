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
OSM SDN controller API handling
"""

from tngsdk.osmclient.common import utils
from tngsdk.osmclient.common import wait as WaitForStatus
from tngsdk.osmclient.common.exceptions import ClientException
from tngsdk.osmclient.common.exceptions import NotFound
import json


class SdnController(object):
    def __init__(self, http=None, client=None):
        self._http = http
        self._client = client
        self._apiName = '/admin'
        self._apiVersion = '/v1'
        self._apiResource = '/sdns'
        self._apiBase = '{}{}{}'.format(self._apiName,
                                        self._apiVersion, self._apiResource)

    # SDNC '--wait' option
    def _wait(self, id, deleteFlag=False):
        # Endpoint to get operation status
        apiUrlStatus = '{}{}{}'.format(self._apiName, self._apiVersion, '/sdns')
        # Wait for status for SDN instance creation/update/deletion
        WaitForStatus.wait_for_status(
            'SDNC',
            str(id),
            WaitForStatus.TIMEOUT_SDNC_OPERATION,
            apiUrlStatus,
            self._http.get2_cmd,
            deleteFlag=deleteFlag)

    def _get_id_for_wait(self, name):
        # Returns id of name, or the id itself if given as argument
        for sdnc in self.list():
            if name == sdnc['_id']:
                return sdnc['_id']
        for sdnc in self.list():
            if name == sdnc['name']:
                return sdnc['_id']
        return ''

    def create(self, name, sdn_controller, wait=False):
        http_code, resp = self._http.post_cmd(endpoint=self._apiBase,
                                       postfields_dict=sdn_controller)
        #print 'HTTP CODE: {}'.format(http_code)
        #print 'RESP: {}'.format(resp)
        if http_code in (200, 201, 202, 204):
            if resp:
                resp = json.loads(resp)
            if not resp or 'id' not in resp:
                raise ClientException('unexpected response from server - {}'.format(
                                      resp))
            if wait:
                # Wait for status for SDNC instance creation
                self._wait(resp.get('id'))
            print(resp['id'])
        else:
            msg = ""
            if resp:
                try:
                    msg = json.loads(resp)
                except ValueError:
                    msg = resp
            raise ClientException("failed to create SDN controller {} - {}".format(name, msg))

    def update(self, name, sdn_controller, wait=False):
        sdnc = self.get(name)
        sdnc_id_for_wait = self._get_id_for_wait(name)
        http_code, resp = self._http.put_cmd(endpoint='{}/{}'.format(self._apiBase,sdnc['_id']),
                                       postfields_dict=sdn_controller)
        # print 'HTTP CODE: {}'.format(http_code)
        # print 'RESP: {}'.format(resp)
        if http_code in (200, 201, 202, 204):
            if wait:
                # In this case, 'resp' always returns None, so 'resp['id']' cannot be used.
                # Use the previously obtained id instead.
                wait_id = sdnc_id_for_wait
                # Wait for status for VI instance update
                self._wait(wait_id)
            else:
                pass
        else:
            msg = ""
            if resp:
                try:
                    msg = json.loads(resp)
                except ValueError:
                    msg = resp
            raise ClientException("failed to update SDN controller {} - {}".format(name, msg))

    def delete(self, name, force=False, wait=False):
        sdn_controller = self.get(name)
        sdnc_id_for_wait = self._get_id_for_wait(name)
        querystring = ''
        if force:
            querystring = '?FORCE=True'
        http_code, resp = self._http.delete_cmd('{}/{}{}'.format(self._apiBase,
                                         sdn_controller['_id'], querystring))
        #print 'HTTP CODE: {}'.format(http_code)
        #print 'RESP: {}'.format(resp)
        if http_code == 202:
            if wait:
                # Wait for status for SDNC instance deletion
                self._wait(sdnc_id_for_wait, deleteFlag=True)
            else:
                print('Deletion in progress')
        elif http_code == 204:
            print('Deleted')
        elif resp and 'result' in resp:
            print('Deleted')
        else:
            msg = ""
            if resp:
                try:
                    msg = json.loads(resp)
                except ValueError:
                    msg = resp
            raise ClientException("failed to delete SDN controller {} - {}".format(name, msg))

    def list(self, filter=None):
        """Returns a list of SDN controllers
        """
        filter_string = ''
        if filter:
            filter_string = '?{}'.format(filter)
        resp = self._http.get_cmd('{}{}'.format(self._apiBase,filter_string))
        #print 'RESP: {}'.format(resp)
        if resp:
            return resp
        return list()

    def get(self, name):
        """Returns an SDN controller based on name or id
        """
        if utils.validate_uuid4(name):
            for sdnc in self.list():
                if name == sdnc['_id']:
                    return sdnc
        else:
            for sdnc in self.list():
                if name == sdnc['name']:
                    return sdnc
        raise NotFound("SDN controller {} not found".format(name))


