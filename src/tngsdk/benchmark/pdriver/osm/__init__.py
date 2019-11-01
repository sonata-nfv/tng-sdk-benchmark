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
from tngsdk.benchmark.helper import parse_ec_parameter_key
import paramiko
import time
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
        self.ip_addresses = {}
        try:
            self.conn_mgr.upload_vnfd_package(ec.vnfd_package_path)
        except:
            LOG.debug("Could not upload vnfd package")
            pass # TODO Handle properly: In a sophisticated (empty) platform, it should give no error.
        try:
            self.conn_mgr.upload_nsd_package(ec.nsd_package_path)
        except:
            LOG.debug("Could not upload nsd package")
            pass # TODO Handle properly: In a sophisticated (empty) platform, it should give no error.

        self.nsi_uuid = (self.conn_mgr.client.nsd.get(ec.experiment.name).get('_id'))
        # Instantiate the NSD
        # TODO Remove hardcoded VIM account name
        self.conn_mgr.client.ns.create(self.nsi_uuid, ec.name, 'OS-DS-BF9', wait=True)

        ns = self.conn_mgr.client.ns.get(ec.name)  # TODO Remove dependency of null NS instances present in OSM
        for vnf_ref in ns.get('constituent-vnfr-ref'):
            vnf_desc = self.conn_mgr.client.vnf.get(vnf_ref)
            for vdur in vnf_desc.get('vdur'):
                self.ip_addresses[vdur.get('vdu-id-ref')]={}
                for interfaces in vdur.get('interfaces'):
                    if interfaces.get('mgmt-vnf')==None:
                        self.ip_addresses[vdur.get('vdu-id-ref')]['mgmt']=interfaces.get('ip-address')
                    else:
                        self.ip_addresses[vdur.get('vdu-id-ref')]['data']=interfaces.get('ip-address')
        # print(self.ip_addresses)
        LOG.info("Instantiated service: {}".format(self.nsi_uuid))

    def execute_experiment(self, ec):

        """
        """
        self.ssh_clients = {}
        vnf_username = self.config.get('main_vm_username')
        vnf_password = self.config.get('main_vm_password')
        probe_username = self.config.get('probe_username')
        probe_password = self.config.get('probe_password')

        # Begin executing commands
        for ex_p in ec.experiment.experiment_parameters:
            cmd_start = ex_p['cmd_start']
            function = ex_p['function']
            self.ssh_clients[function] = paramiko.SSHClient()
            self.ssh_clients[function].set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if function.startswith('mp.'):
                self.ssh_clients[function].connect(self.ip_addresses[function]['mgmt'], username=probe_username,
                                                   password=probe_password)
            else:
                self.ssh_clients[function].connect(self.ip_addresses[function]['mgmt'], username=vnf_username,
                                                   password=vnf_password)
            stdin, stdout, stderr = self.ssh_clients[function].exec_command(cmd_start)
            LOG.info(stdout)
            LOG.info(f"Executing start command {cmd_start}")

    def teardown_experiment(self, ec):
        for ex_p in ec.experiment.experiment_parameters:
            cmd_stop = ex_p['cmd_stop']
            function = ex_p['function']
            self.ssh_clients[function] = paramiko.SSHClient()
            self.ssh_clients[function].set_missing_host_key_policy(paramiko.AutoAddPolicy())
            stdin, stdout, stderr = self.ssh_clients[function].exec_command(cmd_stop)
            LOG.info(f"Executing stop command {cmd_stop}")
            LOG.info(stdout)
        LOG.info("Sleeping for 20 before destroying NS")
        time.sleep(20)
        self.conn_mgr.client.ns.delete(ec.name, wait=True)
        LOG.info("Deleted service: {}".format(self.nsi_uuid))

    def teardown_platform(self, ec):
        pass

    def instantiate_service(self, uuid):
        pass
