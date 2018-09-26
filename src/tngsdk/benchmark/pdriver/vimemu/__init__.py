#  Copyright (c) 2018 SONATA-NFV, 5GTANGO, Paderborn University
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
import logging
import os
import time
from tngsdk.benchmark.pdriver.vimemu.emuc import LLCMClient
from tngsdk.benchmark.pdriver.vimemu.emuc import EmuSrvClient


LOG = logging.getLogger(os.path.basename(__file__))


class VimEmuDriver(object):
    # FIXME Public API of this class is the
    # prototype for the generic driver API.

    def __init__(self, config):
        self.config = config
        self.emusrv_url = ("{}:{}"
                           .format(config.get("host"),
                                   config.get("emusrv_port")))
        self.llcm_url = ("{}:{}"
                         .format(config.get("host"),
                                 config.get("llcm_port")))
        # initialize sub-driver
        self.emusrvc = EmuSrvClient(self.emusrv_url)
        self.llcmc = LLCMClient(self.llcm_url)
        LOG.info("Initialized VimEmuDriver with {}"
                 .format(self.config))

    def setup_platform(self):
        # check connectivity to target
        self.emusrvc.check_platform_ready()

    def setup_experiment(self, ec):
        # start emulator
        self.emusrvc.start_emulation()
        # wait for emulator ready
        self.emusrvc.wait_emulation_ready(self.llcmc)
        # upload package
        self.llcmc.upload_package(ec.package_path)
        # instantiate service
        # wait for service beeing ready
        # setup monitoring?
        pass

    def execute_experiment(self, ec):
        # trigger MP commands
        for i in range(0, 20):
            print("Experiment running ...{}/20".format(i))
            time.sleep(.5)

    def teardown_experiment(self, ec):
        self.emusrvc.stop_emulation()

    def teardown_platform(self):
        pass
