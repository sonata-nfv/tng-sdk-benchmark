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
OSM v1 client API
"""

from tngsdk.osmclient.v1 import vnf
from tngsdk.osmclient.v1 import vnfd
from tngsdk.osmclient.v1 import ns
from tngsdk.osmclient.v1 import nsd
from tngsdk.osmclient.v1 import vim
from tngsdk.osmclient.v1 import package
from tngsdk.osmclient.v1 import vca
from tngsdk.osmclient.v1 import utils
from tngsdk.osmclient.common import http


class Client(object):

    def __init__(
        self,
        host=None,
        so_port=8008,
        so_project='default',
        ro_host=None,
        ro_port=9090,
        upload_port=8443,
            **kwargs):
        self._user = 'admin'
        self._password = 'admin'

        if len(host.split(':')) > 1:
            # backwards compatible, port provided as part of host
            self._host = host.split(':')[0]
            self._so_port = host.split(':')[1]
        else:
            self._host = host
            self._so_port = so_port

        self._so_project = so_project

        http_client = http.Http(
            'https://{}:{}/'.format(
                self._host,
                self._so_port))
        http_client.set_http_header(
            ['Accept: application/vnd.yand.data+json',
             'Content-Type: application/json'])

        self._so_version = self.get_so_version(http_client)

        if ro_host is None:
            ro_host = host
        ro_http_client = http.Http('http://{}:{}/'.format(ro_host, ro_port))
        ro_http_client.set_http_header(
            ['Accept: application/vnd.yand.data+json',
             'Content-Type: application/json'])

        upload_client_url = 'https://{}:{}/composer/upload?api_server={}{}'.format(
                self._host,
                upload_port,
                'https://localhost&upload_server=https://',
                self._host)

        if self._so_version == 'v3':
            upload_client_url = 'https://{}:{}/composer/upload?api_server={}{}&project_name={}'.format(
                self._host,
                upload_port,
                'https://localhost&upload_server=https://',
                self._host,
                self._so_project)

        upload_client = http.Http(upload_client_url)

        self.vnf = vnf.Vnf(http_client, client=self, **kwargs)
        self.vnfd = vnfd.Vnfd(http_client, client=self, **kwargs)
        self.ns = ns.Ns(http=http_client, client=self, **kwargs)
        self.nsd = nsd.Nsd(http_client, client=self, **kwargs)
        self.vim = vim.Vim(
            http=http_client,
            ro_http=ro_http_client,
            client=self,
            **kwargs)
        self.package = package.Package(
            http=http_client,
            upload_http=upload_client,
            client=self,
            **kwargs)
        self.vca = vca.Vca(http_client, client=self, **kwargs)
        self.utils = utils.Utils(http_client, **kwargs)

    @property
    def so_rbac_project_path(self):
        if self._so_version == 'v3':
            return 'project/{}/'.format(self._so_project)
        else:
            return ''

    def get_so_version(self, http_client):
        try:
            resp = http_client.get_cmd('api/operational/version')
            if not resp or 'rw-base:version' not in resp:
                return 'v2'

            if resp['rw-base:version']['version'].split('.')[0] == '5':
                # SO Version 5.x.x.x.x translates to OSM V3
                return 'v3'
            return 'v2'
        except Exception:
            return 'v2'


