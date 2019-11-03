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
OSM SOL005 client API
"""

#from osmclient.v1 import vca
from tngsdk.osmclient.sol005 import vnfd
from tngsdk.osmclient.sol005 import nsd
from tngsdk.osmclient.sol005 import nst
from tngsdk.osmclient.sol005 import nsi
from tngsdk.osmclient.sol005 import ns
from tngsdk.osmclient.sol005 import vnf
from tngsdk.osmclient.sol005 import vim
from tngsdk.osmclient.sol005 import wim
from tngsdk.osmclient.sol005 import package
from tngsdk.osmclient.sol005 import http
from tngsdk.osmclient.sol005 import sdncontroller
from tngsdk.osmclient.sol005 import project as projectmodule
from tngsdk.osmclient.sol005 import user as usermodule
from tngsdk.osmclient.sol005 import role
from tngsdk.osmclient.sol005 import pdud
from tngsdk.osmclient.common.exceptions import ClientException
import json


class Client(object):

    def __init__(
        self,
        host=None,
        so_port=9999,
        user='admin',
        password='admin',
        project='admin',
        **kwargs):

        self._user = user
        self._password = password
        self._project = project
        self._auth_endpoint = '/admin/v1/tokens'
        self._headers = {}

        if len(host.split(':')) > 1:
            # backwards compatible, port provided as part of host
            self._host = host.split(':')[0]
            self._so_port = host.split(':')[1]
        else:
            self._host = host
            self._so_port = so_port

        self._http_client = http.Http(
            'https://{}:{}/osm'.format(self._host,self._so_port))
        self._headers['Accept'] = 'application/json'
        self._headers['Content-Type'] = 'application/yaml'
        http_header = ['{}: {}'.format(key, val)
                       for (key, val) in list(self._headers.items())]
        self._http_client.set_http_header(http_header)

        token = self.get_token()
        if not token:
            raise ClientException(
                    'Authentication error: not possible to get auth token')
        self._headers['Authorization'] = 'Bearer {}'.format(token)
        http_header.append('Authorization: Bearer {}'.format(token))
        self._http_client.set_http_header(http_header)

        self.vnfd = vnfd.Vnfd(self._http_client, client=self)
        self.nsd = nsd.Nsd(self._http_client, client=self)
        self.nst = nst.Nst(self._http_client, client=self)
        self.package = package.Package(self._http_client, client=self)
        self.ns = ns.Ns(self._http_client, client=self)
        self.nsi = nsi.Nsi(self._http_client, client=self)
        self.vim = vim.Vim(self._http_client, client=self)
        self.wim = wim.Wim(self._http_client, client=self)
        self.sdnc = sdncontroller.SdnController(self._http_client, client=self)
        self.vnf = vnf.Vnf(self._http_client, client=self)
        self.project = projectmodule.Project(self._http_client, client=self)
        self.user = usermodule.User(self._http_client, client=self)
        self.role = role.Role(self._http_client, client=self)
        self.pdu = pdud.Pdu(self._http_client, client=self)
        '''
        self.vca = vca.Vca(http_client, client=self, **kwargs)
        self.utils = utils.Utils(http_client, **kwargs)
        '''

    def get_token(self):
        postfields_dict = {'username': self._user,
                           'password': self._password,
                           'project_id': self._project}
        http_code, resp = self._http_client.post_cmd(endpoint=self._auth_endpoint,
                                                     postfields_dict=postfields_dict)
        if http_code not in (200, 201, 202, 204):
            raise ClientException(resp)
        token = json.loads(resp) if resp else None
        if token is not None:
            return token['_id']
        return None

