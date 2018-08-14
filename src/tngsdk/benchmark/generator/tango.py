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
import time
import os
from tngsdk.benchmark.generator import ServiceConfigurationGenerator
import tngsdk.package as tngpkg

LOG = logging.getLogger(__name__)


BASE_PROJECT_PATH = "base_project/"
GEN_PROJECT_PATH = "generated_projects/"


class TangoServiceConfigurationGenerator(
        ServiceConfigurationGenerator):
    """
    5GTANGO Service Configuration Generator.
    Input: 5GTANGO service package.
    Output: 5GTANGO service packages w. applied
    experiment configurations, e.g., resource limits.
    """

    def __init__(self, args):
        self.args = args
        self.RUN_ID = 0
        self.start_time = -1
        LOG.info("5GTANGO service configuration generator initialized")
        LOG.debug("5GTANGO generator args: {}".format(self.args))

    def generate(self, in_pkg_path, func_ex,
                 service_ex):
        """
        Generates service configurations according to the inputs.
        Returns a list of identifiers / paths to the
        generated service configurations.
        """
        if func_ex is not None and len(func_ex):
            # function experiments are not considered
            LOG.warning("Function experiments are not supported!")
        self.start_time = time.time()
        LOG.info("Generating {} service experiments using {}"
                 .format(len(service_ex), in_pkg_path))
        # Step 1: Unpack in_pkg to work_dir/BASE_PROJECT
        base_proj_path = os.path.join(
            self.args.work_dir, BASE_PROJECT_PATH)
        base_proj_path = self._unpack(in_pkg_path, base_proj_path)
        # Step 2: Generate for each experiment
        # Step 3: Package each generated project
        # Step 4: Return (TODO check what is really needed and refactor)
        return dict()

    def _unpack(self, pkg_path, proj_path):
        args = [
            "--unpackage", pkg_path,
            "--output", proj_path,
            "--store-backend", "TangoProjectFilesystemBackend"
        ]
        # call the package component
        r = tngpkg.run(args)
        if r.error is not None:
            raise BaseException("Can't read package {}".format(pkg_path))
        # return the full path to the project
        proj_path = r.metadata.get("_storage_location")
        LOG.info("Unpacked {} to {}".format(pkg_path, proj_path))
        return proj_path

    def _pack(proj_path, pkg_path):
        pass
