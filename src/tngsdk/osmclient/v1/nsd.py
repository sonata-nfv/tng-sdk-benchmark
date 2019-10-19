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
OSM nsd API handling
"""

from osmclient.common.exceptions import NotFound
from osmclient.common.exceptions import ClientException


class Nsd(object):

    def __init__(self, http=None, client=None):
        self._http = http
        self._client = client

    def list(self):
        resp = self._http.get_cmd('api/running/{}nsd-catalog/nsd'
                .format(self._client.so_rbac_project_path))
        
        if self._client._so_version == 'v3':
            if resp and 'project-nsd:nsd' in resp:
                return resp['project-nsd:nsd']
        else:
            # Backwards Compatibility
            if resp and 'nsd:nsd' in resp:
                return resp['nsd:nsd']

        return list()

    def get(self, name):
        for nsd in self.list():
            if name == nsd['name']:
                return nsd
        raise NotFound("cannot find nsd {}".format(name))

    def delete(self, nsd_name):
        nsd = self.get(nsd_name)
        if nsd is None:
            raise NotFound("cannot find nsd {}".format(nsd_name))

        resp = self._http.delete_cmd(
            'api/running/{}nsd-catalog/nsd/{}'
            .format(self._client.so_rbac_project_path, nsd['id']))
        if 'success' not in resp:
            raise ClientException("failed to delete nsd {}".format(nsd_name))
