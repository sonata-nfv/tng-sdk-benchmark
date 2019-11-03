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
OSM pdud API handling
"""

from tngsdk.osmclient.common.exceptions import NotFound
from tngsdk.osmclient.common.exceptions import ClientException
from tngsdk.osmclient.common import utils
import json


class Pdu(object):

    def __init__(self, http=None, client=None):
        self._http = http
        self._client = client
        self._apiName = '/pdu'
        self._apiVersion = '/v1'
        self._apiResource = '/pdu_descriptors'
        self._apiBase = '{}{}{}'.format(self._apiName,
                                        self._apiVersion, self._apiResource)

    def list(self, filter=None):
        filter_string = ''
        if filter:
            filter_string = '?{}'.format(filter)
        resp = self._http.get_cmd('{}{}'.format(self._apiBase,filter_string))
        if resp:
            return resp
        return list()

    def get(self, name):
        if utils.validate_uuid4(name):
            for pdud in self.list():
                if name == pdud['_id']:
                    return pdud
        else:
            for pdud in self.list():
                if 'name' in pdud and name == pdud['name']:
                    return pdud
        raise NotFound("pdud {} not found".format(name))

    def get_individual(self, name):
        pdud = self.get(name)
        # It is redundant, since the previous one already gets the whole pdudInfo
        # The only difference is that a different primitive is exercised
        resp = self._http.get_cmd('{}/{}'.format(self._apiBase, pdud['_id']))
        #print yaml.safe_dump(resp)
        if resp:
            return resp
        raise NotFound("pdu {} not found".format(name))

    def delete(self, name, force=False):
        pdud = self.get(name)
        querystring = ''
        if force:
            querystring = '?FORCE=True'
        http_code, resp = self._http.delete_cmd('{}/{}{}'.format(self._apiBase,
                                         pdud['_id'], querystring))
        #print 'HTTP CODE: {}'.format(http_code)
        #print 'RESP: {}'.format(resp)
        if http_code == 202:
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
            raise ClientException("failed to delete pdu {} - {}".format(name, msg))

    def create(self, pdu, update_endpoint=None):
        headers= self._client._headers
        headers['Content-Type'] = 'application/yaml'
        http_header = ['{}: {}'.format(key,val)
                      for (key,val) in list(headers.items())]
        self._http.set_http_header(http_header)
        if update_endpoint:
            http_code, resp = self._http.put_cmd(endpoint=update_endpoint, postfields_dict=pdu)
        else:
            endpoint = self._apiBase
            #endpoint = '{}{}'.format(self._apiBase,ow_string)
            http_code, resp = self._http.post_cmd(endpoint=endpoint, postfields_dict=pdu)
        #print 'HTTP CODE: {}'.format(http_code)
        #print 'RESP: {}'.format(resp)
        if http_code in (200, 201, 202, 204):
            if resp:
                resp = json.loads(resp)
            if not resp or 'id' not in resp:
                raise ClientException('unexpected response from server: '.format(
                                      resp))
            print(resp['id'])
        else:
            msg = "Error {}".format(http_code)
            if resp:
                try:
                    msg = "{} - {}".format(msg, json.loads(resp))
                except ValueError:
                    msg = "{} - {}".format(msg, resp)
            raise ClientException("failed to create/update pdu - {}".format(msg))

    def update(self, name, filename):
        pdud = self.get(name)
        endpoint = '{}/{}'.format(self._apiBase, pdud['_id'])
        self.create(filename=filename, update_endpoint=endpoint)

