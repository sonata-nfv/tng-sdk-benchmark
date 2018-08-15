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
import shutil
import os
from tngsdk.benchmark.generator import ServiceConfigurationGenerator
from tngsdk.benchmark.helper import ensure_dir
import tngsdk.package as tngpkg

LOG = logging.getLogger(__name__)
# decrease the loglevel of the packager tool
logging.getLogger("packager.py").setLevel(logging.WARNING)


BASE_PROJECT_PATH = "base_project/"
GEN_PROJECT_PATH = "gen_projects/"
GEN_PKG_PATH = "gen_pkgs/"


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
        for ex in service_ex:
            self._generate_projects(base_proj_path, ex)
        # Step 3: Package each generated project
        # Step 4: Return (TODO check what is really needed and refactor)
        return dict()

    def _unpack(self, pkg_path, proj_path):
        """
        Wraps the tng-sdk-package unpacking functionality.
        """
        args = [
            "--unpackage", pkg_path,
            "--output", proj_path,
            "--store-backend", "TangoProjectFilesystemBackend",
            "--quiet"
        ]
        # call the package component
        r = tngpkg.run(args)
        if r.error is not None:
            raise BaseException("Can't read package {}: {}"
                                .format(pkg_path, r.error))
        # return the full path to the project
        proj_path = r.metadata.get("_storage_location")
        LOG.debug("Unpacked {} to {}".format(pkg_path, proj_path))
        return proj_path

    def _pack(self, proj_path, pkg_path):
        """
        Wraps the tng-sdk-package packaging functionality.
        """
        args = [
            "--package", proj_path,
            "--output", pkg_path,
            "--store-backend", "TangoProjectFilesystemBackend",
            "--quiet"
        ]
        # call the package component
        r = tngpkg.run(args)
        if r.error is not None:
            raise BaseException("Can't create package {}: {}"
                                .format(pkg_path, r.error))
        # return the full path to the package
        pkg_path = r.metadata.get("_storage_location")
        LOG.debug("Packed {} to {}".format(proj_path, pkg_path))
        return pkg_path

    def _generate_projects(self, base_proj_path, ex):
        LOG.info("Generating {} projects for {}"
                 .format(len(ex.experiment_configurations), ex))
        # iterate over all experiment configurations
        n_done = 0
        for ec in ex.experiment_configurations:
            # 1. create project by copying base_proj
            self._copy_project(base_proj_path, ec)
            # 2. add MPs to project
            self._add_mps_to_project(ec)
            # 3. apply configuration parameters to project
            self._add_params_to_project(ec)
            # 4. package project
            self._package_project(ec)
            # 5. status output
            n_done += 1
            LOG.info("Generated project ({}/{}): {}"
                     .format(n_done,
                             len(ex.experiment_configurations),
                             os.path.basename(ec.package_path)))

    def _copy_project(self, base_proj_path, ec):
        ec.project_path = os.path.join(
            self.args.work_dir, GEN_PROJECT_PATH, ec.name)
        LOG.debug("Created project: {}".format(ec.project_path))
        shutil.copytree(base_proj_path, ec.project_path)

    def _add_mps_to_project(self, ec):
        """
        Extend a project's VNFFG with the MPs.
        """
        pass

    def _add_params_to_project(self, ec):
        """
        Apply parameters, like resource limits, commands,
        to the project descriptors.
        """
        pass

    def _package_project(self, ec):
        """
        Package the project of the given experiment configuration.
        """
        tmp = os.path.join(
            self.args.work_dir, GEN_PKG_PATH)
        ensure_dir(tmp)
        ec.package_path = "{}{}.tgo".format(tmp, ec.name)
        self._pack(ec.project_path, ec.package_path)
