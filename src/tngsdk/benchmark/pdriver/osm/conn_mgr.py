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
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from osmclient import client
from osmclient.common.exceptions import ClientException
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
LOG = TangoLogger.getLogger(__name__)


class OSMConnectionManager(object):
    """
    OSM Connection Manager class
    """

    def __init__(self, config):
        self.hostname = config.get("osm_host")
        self.username = config.get("username")
        self.password = config.get("password")
        self.project = config.get("project")

        self.kwargs = {}

        if self.username is not None:
            self.kwargs['user'] = self.username
        if self.password is not None:
            self.kwargs['password'] = self.password
        if self.project is not None:
            self.kwargs['project'] = self.project

    def connect(self):
        self.client = client.Client(host=self.hostname, sol005=True, **self.kwargs)
        if self.client:
            return True
        else:
            return False

    def upload_vnfd_package(self, package_path):
        # re-init client
        self.client = client.Client(host=self.hostname, sol005=True, **self.kwargs)
        self.client.vnfd.create(package_path)
        
    
    def upload_nsd_package(self, package_path, package_name = None):
        # re-init client
        self.client = client.Client(host=self.hostname, sol005=True, **self.kwargs)
        self.client.nsd.create(package_path)
    