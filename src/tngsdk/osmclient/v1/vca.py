# Copyright 2017 Sandvine
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
OSM VCA API handling
"""

from osmclient.common.exceptions import ClientException


class Vca(object):

    def __init__(self, http=None, client=None):
        self._http = http
        self._client = client

    def list(self):
        resp = self._http.get_cmd('api/config/{}config-agent'
                .format(self._client.so_rbac_project_path))
        if resp and 'rw-config-agent:config-agent' in resp:
            return resp['rw-config-agent:config-agent']['account']
        return list()

    def delete(self, name):
        if ('success' not in
            self._http.delete_cmd('api/config/{}config-agent/account/{}'
                                  .format(self._client.so_rbac_project_path, name))):
            raise ClientException("failed to delete config agent {}"
                                  .format(name))

    def create(self, name, account_type, server, user, secret):
        postdata = {}
        postdata['account'] = list()

        account = {}
        account['name'] = name
        account['account-type'] = account_type
        account['juju'] = {}
        account['juju']['user'] = user
        account['juju']['secret'] = secret
        account['juju']['ip-address'] = server
        postdata['account'].append(account)

        if 'success' not in self._http.post_cmd('api/config/{}config-agent'
                                .format(self._client.so_rbac_project_path), postdata):
            raise ClientException("failed to create config agent {}"
                                  .format(name))
