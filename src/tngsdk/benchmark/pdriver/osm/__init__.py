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
from tngsdk.benchmark.pdriver.osm.conn_mgr import OSMConnectionManager
from tngsdk.benchmark.logger import TangoLogger
LOG = TangoLogger.getLogger(__name__)


class OsmDriver(object):
    """
    PDRIVER Class to allow connection to Open Source MANO (OSM)
    """

    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.conn_mgr = OSMConnectionManager(self.config)
        self.conn_mgr.connect()
        if self.conn_mgr.connect():
            LOG.info("Connection to OSM Established.")
        else:
            LOG.error('Connection to OSM Failed!')
            raise Exception()

    def setup_platform(self):
        return True  # for now

    def setup_experiment(self, ec):
        # package_id = self.conn_mgr.upload_package(package_path)
        self.ip_addresses=[]
        try:
            self.conn_mgr.upload_vnfd_package(ec.vnfd_package_path)
        except:
            pass #TODO Handle properly: In a sophisticated (empty) platform, it should give no error.
        try:
            self.conn_mgr.upload_nsd_package(ec.nsd_package_path)
        except:
            pass #TODO Handle properly: In a sophisticated (empty) platform, it should give no error.

        self.uuid=(self.conn_mgr.client.nsd.get('example_1vnf_ns').get('_id')) #TODO Remove hardcoded nsd name
        # Instantiate the NSD
        self.conn_mgr.client.ns.create(self.uuid, ec.name, 'openstacl-VIM-2', wait=True) #TODO Remove hardcoded VIM account name

        ns = self.conn_mgr.client.ns.get(ec.name) #TODO Remove dependency of null NS instances present in OSM
        for vnf_ref in ns.get('constituent-vnfr-ref'):
            vnf_desc = self.conn_mgr.client.vnf.get(vnf_ref)
            for vdur in vnf_desc.get('vdur'):
                for interfaces in vdur.get('interfaces'):
                    if interfaces.get('mgmt-vnf')==None:
                        self.ip_addresses.append(interfaces.get('ip-address'))
        print(self.ip_addresses)

        # LOG.info("Instantiated service: {}".format(self.nsi_uuid))
        pass

    def execute_experiment(self, ec):
        pass

    def teardown_experiment(self, ec):
        pass

    def instantiate_service(self, uuid):
        pass
