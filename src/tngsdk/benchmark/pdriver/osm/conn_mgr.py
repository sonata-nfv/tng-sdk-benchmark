#  Copyright (c) 2019 SONATA-NFV, 5GTANGO, Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, 5GTANGO, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
#
# This work has also been performed in the framework of the 5GTANGO project,
# funded by the European Commission under Grant number 761493 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.5gtango.eu).

import requests
from tngsdk.benchmark.logger import TangoLogger


LOG = TangoLogger.getLogger(__name__)


class OSMConnectionManager(object):
    """
    OSM Connection Manager class
    """

    def __init__(self, config):
        self.host = ("http://{}:{}/osm"
                     .format(config.get("osm_host"),
                             config.get("osm_port")))
        self.username = config.get("username")
        self.password = config.get("password")
        self.project_id = config.get("project_id")
        self.header = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.token = None

    def connect(self):
        if not self.token:
            return self._get_token()
        else:
            return True

    def _get_token(self):
        request = {
            "username": self.username,
            "password": self.password,
            "project_id": self.project_id
        }
        dest = '/admin/v1/tokens'
        result = self._request("POST", dest, request, self.header).json()
        if result:
            self.token = result["_id"]
            self.header["Authorization"] = "Bearer {}".format(self.token)

    def _request(self, method, url, payload, headers):
        _url = self.host + url
        response = requests.request(method, _url, json=payload, verify=False,
                                    headers=self.header)
        if response.ok:
            return response
        else:
            return False

    def list_ns_instances(self):
        url = '/nslcm/v1/ns_instances_content'
        payload = None
        result = self._api_call("GET", url, payload, self.header).json()
        return result

    def add_networkservice(self, nsdId, nsName, nsDescription, vimAccountId):
        url = '/nslcm/v1/ns_instances_content'
        payload = {
            "nsdId": nsdId,
            "nsName": nsName,
            "nsDescription": nsDescription,
            "vimAccountId": vimAccountId
        }
        res = self._api_call("POST", url, payload, self.header)
        # pdb.set_trace()
        if res.status_code == 201:
            result = res.json()
            # Return ID of created NS
            return result["id"]

    def delete_networkservice(self, nsid):
        url = "/nslcm/v1/ns_instances/{}/terminate".format(nsid)
        payload = None
        # pdb.set_trace()
        res = self._api_call("POST", url, payload, self.header)
        if res.status_code == 201:
            # Return True if NS is deleted
            return True
        else:
            return False

    def remove_networkservice(self, nsid):
        url = "/nslcm/v1/ns_instances/{}".format(nsid)
        # pdb.set_trace()
        res = self._api_call("DELETE", url, None, self.header)
        if res:  # Faulty
            return True
        else:
            return False
