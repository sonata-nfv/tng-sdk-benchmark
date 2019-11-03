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
import os
import json
from tngsdk.benchmark.logger import TangoLogger
from tngsdk.benchmark.helper import ensure_dir
from tngsdk.benchmark.pdriver.vimemu import VimEmuDriver
from tngsdk.benchmark.pdriver.osm import OsmDriver

LOG = TangoLogger.getLogger(__name__)


PATH_EC_FILE = "ex_config.json"


class Executor(object):

    def __init__(self, args, ex_list):
        self.args = args
        # list of experiments to execute
        self.ex_list = ex_list
        LOG.info("Initialized executor with {} experiments and {} configs"
                 .format(len(self.ex_list),
                         [len(ex.experiment_configurations)
                          for ex in self.ex_list]))
        LOG.debug("Config: {}".format(self.args.config))
        # load pdriver module to be used
        self.pd = None
        # FIXME only load the "default" target for now
        for t in self.args.config.get("targets"):
            if t.get("name") == "default":
                self.pd = self._load_pdriver(t)

    def _load_pdriver(self, t):
        # TODO: Load osm pdriver here
        if t.get("pdriver") == "vimemu":
            return VimEmuDriver(self.args, t.get("pdriver_config"))
        elif t.get("pdriver") == "osm":
            return OsmDriver(self.args, t.get("pdriver_config"))
        else:
            raise BaseException("Platform driver '{}' not supported."
                                .format(t.get("pdriver")))
        return None

    def _write_experiment_configuration(self, ec):
        """
        Write the used experiment configuration to disk.
        """
        dst_path = os.path.join(self.args.result_dir, ec.name)
        dst_path = os.path.join(dst_path, PATH_EC_FILE)
        ensure_dir(dst_path)
        LOG.debug("Writing ex. configuration: {}".format(dst_path))
        data = {
            "name": ec.name,
            "run_id": ec.run_id,
            "parameter": ec.parameter,
            "project_path": ec.project_path,
            # "package_path": ec.package_path #TODO This statement is for VIMEMU but is creating problem for OSM,
            # find some workaround
        }
        with open(dst_path, "w") as f:
            json.dump(data, f)

    def setup(self):
        """
        Prepare the target platform.
        """
        LOG.info("Preparing target platforms")
        self.pd.setup_platform()

    def run(self):
        """
        Executes all experiments and configurations.
        """
        LOG.info("Executing experiments")
        # match to targets (TODO assignment problem)
        t_pd = self.pd
        # iterate over experiments/configs and execute
        for ex in self.ex_list:
            for ec in ex.experiment_configurations:
                self._write_experiment_configuration(ec)
                LOG.info("Setting up '{}'".format(ec))
                t_pd.setup_experiment(ec)
                LOG.info("Executing '{}'".format(ec))
                t_pd.execute_experiment(ec)
                LOG.info("Teardown '{}'".format(ec))
                t_pd.teardown_experiment(ec)

    def teardown(self):
        """
        Clean up target platform.
        """
        LOG.info("Teardown target platforms")
        self.pd.teardown_platform()
