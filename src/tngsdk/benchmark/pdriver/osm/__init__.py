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
            LOG.info("Connection Established")
        else:
            LOG.error('Connection to OSM failed!')
            raise Exception()
    
    def setup_platform(self):
        return True  # for now

    def setup_experiment(self, ec):
        package_id = self.conn_mgr.upload_package(package_path)


    def setup_experiment(self, ec):
        # start emulator
        self.emusrvc.start_emulation()
        # wait for emulator ready
        self.emusrvc.wait_emulation_ready(self.llcmc)
        # upload package
        ns_uuid = self.llcmc.upload_package(ec.package_path)
        # instantiate service
        self.nsi_uuid = self.llcmc.instantiate_service(ns_uuid)
        LOG.info("Instantiated service: {}".format(self.nsi_uuid))

    def execute_experiment(self, ec):
        # start container monitoring (dedicated thread)
        # depricated: we use prometheus + cadvisor now
        # self.emudocker_mon = EmuDockerMonitor(
        #    self.emudocker, self._experiment_wait_time(ec))
        # self.emudocker_mon.daemon = True
        # self.emudocker_mon.start()
        # collect commands for MPs
        mp_in_cmd_start = ec.parameter.get("{}cmd_start".format(MP_IN_KEY))
        mp_in_cmd_stop = ec.parameter.get("{}cmd_stop".format(MP_IN_KEY))
        mp_out_cmd_start = ec.parameter.get("{}cmd_start".format(MP_OUT_KEY))
        mp_out_cmd_stop = ec.parameter.get("{}cmd_stop".format(MP_OUT_KEY))
        # collect commands for VNFs
        vnf_cmd_start_dict, vnf_cmd_stop_dict = self._collect_vnf_commands(ec)
        # trigger MP/function commands: we always execute the commands in the
        # following order:
        # 1. vnf_cmd_start
        # 2. mp_out_cmd_start
        # 3. mp_in_cmd_start
        # - run the experiment -
        # 4. mp_in_cmd_stop
        # 5. mp_out_cmd_stop
        # 6. vnf_cmd_stop
        # FIXME make this user-configurable and more flexible
        LOG.debug("Executing start commands inside containers ...")
        for vnf_cname, cmd in vnf_cmd_start_dict.items():
            self.emudocker.execute(vnf_cname, cmd,
                                   os.path.join(PATH_SHARE,
                                                PATH_CMD_START_LOG))
        # give the VNF time to start: wait for "time_warmup"
        time_warmup = int(ec.parameter.get(
            "ep::header::all::time_warmup"))
        LOG.info("Warmup period ({}s) ...".format(time_warmup))
        time.sleep(time_warmup)
        LOG.info("Stimulating ...")
        self.emudocker.execute(MP_OUT_NAME, mp_out_cmd_start,
                               os.path.join(PATH_SHARE, PATH_CMD_START_LOG))
        self.emudocker.execute(MP_IN_NAME, mp_in_cmd_start,
                               os.path.join(PATH_SHARE, PATH_CMD_START_LOG))
        self.t_experiment_start = datetime.datetime.now()
        self._wait_experiment(ec)
        self.t_experiment_stop = datetime.datetime.now()
        # hold execution for manual debugging:
        if self.args.hold_and_wait_for_user:
            input("Press Enter to continue...")
        LOG.debug("Executing stop commands inside containers ...")
        self.emudocker.execute(MP_IN_NAME, mp_in_cmd_stop,
                               os.path.join(PATH_SHARE,
                                            PATH_CMD_STOP_LOG), block=True)
        self.emudocker.execute(MP_OUT_NAME, mp_out_cmd_stop,
                               os.path.join(PATH_SHARE,
                                            PATH_CMD_STOP_LOG), block=True)
        for vnf_cname, cmd in vnf_cmd_stop_dict.items():
            self.emudocker.execute(vnf_cname, cmd,
                                   os.path.join(PATH_SHARE,
                                                PATH_CMD_STOP_LOG), block=True)
        self._wait_time(WAIT_SHUTDOWN_TIME,
                        "Finalizing experiment '{}'".format(ec))
        # wait for monitoring thread to finalize
        # LOG.debug("Waiting for container monitoring thread ...")
        # self.emudocker_mon.join()
        # collect results
        self._collect_experiment_results(ec)
        LOG.info("Finalized '{}'".format(ec))
    def instantiate_service(self, uuid):
        pass