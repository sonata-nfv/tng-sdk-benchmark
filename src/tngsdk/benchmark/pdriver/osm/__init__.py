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
import os
import stat
import scp
from tngsdk.benchmark.helper import write_yaml
LOG = TangoLogger.getLogger(__name__)

PATH_SHARE = "tngbench_share"
PATH_CMD_START_LOG = "cmd_start.log"
PATH_CMD_STOP_LOG = "cmd_stop.log"


class OsmDriver(object):
    """
    PDRIVER Class to allow connection to Open Source MANO (OSM)
    """

    def __init__(self, args, config):
        self.main_vm_data_ip = None
        self.args = args
        self.config = config
        self.conn_mgr = OSMConnectionManager(self.config)
        # self.conn_mgr.connect()
        if self.conn_mgr.connect():
            LOG.info("Connection to OSM Established.")
        else:
            LOG.error('Connection to OSM Failed!')
            raise Exception()

    def setup_platform(self):
        pass
        # vim_access={}
        # vim_access['vim-type'] = "openstack"
        # vim_access['description'] = "description"
        # vim_access['vim-url'] = "http://fgcn-backflip9.cs.upb.de/identity/v3"
        # vim_access['vim-username'] = "admin"
        # vim_access['vim-password'] = "admin"
        # vim_access['vim-tenant-name'] = "admin"

        # vim_config = {"use_floating_ip":True}
        # write_yaml('/tmp/temp_vim_config.yaml', vim_config)
        # vim_access['config'] = open(r'/tmp/temp_vim_config.yaml')
        # try:
        #     self.conn_mgr.client.vim.create("openstack-site", vim_access, wait=True)
        # except Exception:
        #     pass

    def setup_experiment(self, ec):
        self.ip_addresses = {}
        try:
            self.vnfd_id = self.conn_mgr.upload_vnfd_package(ec.vnfd_package_path)
        except Exception:
            LOG.error("Could not upload vnfd package")
            exit(1)
            # pass  # TODO Handle properly: In a sophisticated (empty) platform, it should give no error.
        try:
            self.nsd_id = self.conn_mgr.upload_nsd_package(ec.nsd_package_path)
        except Exception:
            LOG.error("Could not upload nsd package")
            exit(1)
            # pass  # TODO Handle properly: In a sophisticated (empty) platform, it should give no error.

        self.nsi_uuid = (self.conn_mgr.client.nsd.get(ec.experiment.name).get('_id'))
        # Instantiate the NSD
        # TODO Remove hardcoded VIM account name
        self.conn_mgr.client.ns.create(self.nsi_uuid, ec.name, 'OS-DS-BF9', wait=True)

        ns = self.conn_mgr.client.ns.get(ec.name)  # TODO Remove dependency of null NS instances present in OSM
        for vnf_ref in ns.get('constituent-vnfr-ref'):
            vnf_desc = self.conn_mgr.client.vnf.get(vnf_ref)
            for vdur in vnf_desc.get('vdur'):
                self.ip_addresses[vdur.get('vdu-id-ref')] = {}
                for interfaces in vdur.get('interfaces'):
                    if interfaces.get('mgmt-vnf') is None:
                        if vdur.get('vdu-id-ref').startswith('mp.'):
                            self.main_vm_data_ip = interfaces.get('ip-address')
                        self.ip_addresses[vdur.get('vdu-id-ref')]['data'] = interfaces.get('ip-address')
                    else:
                        self.ip_addresses[vdur.get('vdu-id-ref')]['mgmt'] = interfaces.get('ip-address')
        # print(self.ip_addresses)
        LOG.info("Instantiated service: {}".format(self.nsi_uuid))

    def execute_experiment(self, ec):

        """
        Execute the experiment
        """
        self.ssh_clients = {}
        vnf_username = self.config.get('main_vm_username')
        vnf_password = self.config.get('main_vm_password')
        probe_username = self.config.get('probe_username')
        probe_password = self.config.get('probe_password')

        login_uname = None
        login_pass = None
        # Begin executing commands
        time_warmup = int(ec.parameter['ep::header::all::time_warmup'])
        LOG.debug(f'Warmup time: Sleeping for {time_warmup}')
        time.sleep(time_warmup)
        for ex_p in ec.experiment.experiment_parameters:
            cmd_start = ex_p['cmd_start']
            function = ex_p['function']

            if function.startswith('mp.'):
                login_uname = probe_username
                login_pass = probe_password
            else:
                login_uname = vnf_username
                login_pass = vnf_password

            while not self._ssh_connect(function, self.ip_addresses[function]['mgmt'], username=login_uname,
                                        password=login_pass):
                # Keep looping until a connection is there
                continue

            LOG.info(f"Executing start command {cmd_start}")
            global PATH_SHARE
            PATH_SHARE = os.path.join('/', 'home', login_uname, PATH_SHARE)
            stdin, stdout, stderr = self.ssh_clients[function].exec_command(
                f'mkdir {PATH_SHARE}')
            stdin, stdout, stderr = self.ssh_clients[function].exec_command(
                f'{cmd_start} &> {PATH_SHARE}/{PATH_CMD_START_LOG} &')

            LOG.info(stdout)

    def _ssh_connect(self, function_name, ip_address, username, password):
        try:
            self.ssh_clients[function_name] = paramiko.SSHClient()
            self.ssh_clients[function_name].set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_clients[function_name].connect(ip_address, username=username,
                                                    password=password, look_for_keys=False)
        except TimeoutError:
            return False
        except paramiko.ssh_exception.NoValidConnectionsError:
            return False
        except paramiko.ssh_exception.BadAuthenticationType:
            return False
        except paramiko.ssh_exception.SSHException:
            return False
        return True

    def teardown_experiment(self, ec):
        # Sleep for experiment duration
        experiment_duration = int(ec.parameter['ep::header::all::time_limit'])
        LOG.info(f'Experiment duration: Sleeping for {experiment_duration} before stopping')
        time.sleep(experiment_duration)
        for ex_p in ec.experiment.experiment_parameters:
            cmd_stop = ex_p['cmd_stop']
            function = ex_p['function']
            # self.ssh_clients[function] = paramiko.SSHClient()
            # self.ssh_clients[function].set_missing_host_key_policy(paramiko.AutoAddPolicy())
            LOG.info(f"Executing stop command {cmd_stop}")
            stdin, stdout, stderr = self.ssh_clients[function].exec_command(
                f'{cmd_stop} &> {PATH_SHARE}/{PATH_CMD_STOP_LOG} &')
            self._collect_experiment_results(ec, function)
            LOG.info(stdout)
        LOG.info("Sleeping for 20 before destroying NS")
        time.sleep(20)
        self.conn_mgr.client.ns.delete(ec.name, wait=True)
        self.conn_mgr.client.nsd.delete(self.nsd_id)
        self.conn_mgr.client.vnfd.delete(self.vnfd_id)
        LOG.info("Deleted service: {}".format(self.nsi_uuid))

    def teardown_platform(self, ec):
        # self.conn_mgr.client.vim.delete("trial_vim")
        pass

    def instantiate_service(self, uuid):
        pass

    def _collect_experiment_results(self, ec, function):
        LOG.info("Collecting experiment results ...")
        remote_dir = f'{PATH_SHARE}/'
        # generate result paths
        dst_path = os.path.join(self.args.result_dir, ec.name)
        # for each container collect files from containers
        function_dst_path = os.path.join(dst_path, function)
        os.makedirs(function_dst_path, exist_ok=True)

        local_dir = f'{function_dst_path}/'
        scp_client = scp.SCPClient(self.ssh_clients[function].get_transport())

        scp_client.get(remote_dir, local_dir, recursive=True)
