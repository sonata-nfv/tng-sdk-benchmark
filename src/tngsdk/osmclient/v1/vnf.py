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
OSM vnf API handling
"""

from tngsdk.osmclient.common.exceptions import NotFound


class Vnf(object):
    def __init__(self, http=None, client=None):
        self._http = http
        self._client = client

    def list(self):
        resp = self._http.get_cmd('v1/api/operational/{}vnfr-catalog/vnfr'
                .format(self._client.so_rbac_project_path))
        if resp and 'vnfr:vnfr' in resp:
            return resp['vnfr:vnfr']
        return list()

    def get(self, vnf_name):
        vnfs = self.list()
        for vnf in vnfs:
            if vnf_name == vnf['name']:
                return vnf
            if vnf_name == vnf['id']:
                return vnf
        raise NotFound("vnf {} not found".format(vnf_name))

    def get_monitoring(self, vnf_name):
        vnf = self.get(vnf_name)
        if vnf and 'monitoring-param' in vnf:
            return vnf['monitoring-param']
        return None
