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
from tngsdk.benchmark.helper import ensure_dir, download_file


LOG = logging.getLogger(__name__)


BD_TEMPLATE_PATH = "/tmp/tng-bench/vnf-bd.yaml"


class IetfBmwgResultProcessor(object):

    def __init__(self, args, service_experiments):
        self.args = args
        self.service_experiments = service_experiments
        # fetch BD template from GitHub
        if not download_file("https://raw.githubusercontent.com/mpeuster/"
                             + "vnf-bench-model/master/experiments/vnf-br/"
                             + "templates/vnf-bd.yaml",
                             BD_TEMPLATE_PATH):
            # TODO this is temporary, don't rely on online resources
            raise BaseException("Could not download BD template. Abort.")

    def run(self):
        # check inputs and possibly skip
        if self.args.ibbd_dir is None:
            LOG.info("IETF BMWG BD dir not specified (--ibbd). Skipping.")
            return
        # generate IETF BMWG BD, PP, BR
        for ex in self.service_experiments:
            # iterate over all experiment configurations
            for ec in ex.experiment_configurations:
                # generate assets
                bd = self._generate_bd(ec)
                pp = self._generate_pp(ec)
                self._generate_br(ec, bd, pp)

    def _generate_bd(self, ec):
        # output path for YAML file
        path = os.path.join(self.args.ibbd_dir,
                            "{}-bd.yaml".format(ec.name))
        # TODO render BD using template
        bd = dict()
        # TODO write BD
        ensure_dir(path)
        LOG.debug("Generated IETF BMWG BD: {}".format(path))
        return bd

    def _generate_pp(self, ec):
        return dict()

    def _generate_br(self, ec, bd, pp):
        pass
