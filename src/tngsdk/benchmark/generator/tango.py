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
from tngsdk.benchmark.helper import ensure_dir, read_yaml, write_yaml
import tngsdk.package as tngpkg

LOG = logging.getLogger(__name__)
# decrease the loglevel of the packager tool
logging.getLogger("packager.py").setLevel(logging.WARNING)


BASE_PROJECT_PATH = "base_project/"
GEN_PROJECT_PATH = "gen_projects/"
GEN_PKG_PATH = "gen_pkgs/"
TEMPLATE_VNFD_MP = "template/tango_vnfd_mp.yml"


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
        Extend a project's VNFFG with the MPs
        and add the MPs as new VNFs.
        """
        ex = ec.experiment
        for mp in ex.measurement_points:
            # 1. add MP VNFDs to project
            self._add_mp_vnfd_to_project(mp, ec)
            # 2. extend NSD
            self._add_mp_to_nsd(mp, ec)

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

    def _add_mp_vnfd_to_project(self, mp, ec,
                                template=TEMPLATE_VNFD_MP):
        """
        Uses templates/tango_vnfd_mp.yml as basis,
        extends it and stores it in project folder.
        Finally the project.yml is updated.
        """
        tpath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), template)
        vnfd = read_yaml(tpath)
        # TODO better use template engine like Jinja
        # replace placeholder fields (this highly depends on used template!)
        vnfd["name"] = mp.get("name")
        # allow different containers as parameter study
        vnfd["virtual_deployment_units"][0]["vm_image"] = mp.get("container")
        # write vnfd to project
        vname = "{}.yaml".format(mp.get("name"))
        write_yaml(os.path.join(ec.project_path, vname), vnfd)
        # add vnfd to project.yml
        ppath = os.path.join(ec.project_path, "project.yml")
        projd = read_yaml(ppath)
        projd.get("files").append({
            "path": vname,
            "type": "application/vnd.5gtango.vnfd",
            "tags": ["eu.5gtango", "mp"]
        })
        write_yaml(ppath, projd)
        LOG.debug("Added MP VNFD {} to project {}"
                  .format(vname, projd.get("name")))

    def _add_mp_to_nsd(self, mp, ec):
        """
        Add MP to NSD:
        - add VNF to functions section
        - connect measurement points w. virt. links
        - update forwarding graph
        """
        # 1. load NSD
        nsd = read_yaml(self._get_nsd_path(ec))
        # 2. add MP VNF to NSD
        nsd.get("network_functions").append({
                "vnf_id": mp.get("name"),
                "vnf_name": mp.get("name"),
                "vnf_vendor": "eu.5gtango.benchmark",
                "vnf_version": "1.0"
        })
        # 3. connect measurement point to service (replace virt. links)
        mp_cp = mp.get("connection_point")
        new_cp = "{}:data".format(mp.get("name"))
        for vl in nsd.get("virtual_links"):
            cprs = vl.get("connection_points_reference")
            # replace ns in/out link endpoints in NSD
            for i in range(0, len(cprs)):
                if cprs[i] == mp_cp:
                    cprs[i] = new_cp
                    LOG.debug(
                        "Replaced virtual link CPR '{}' by '{}'"
                        .format(mp_cp, cprs[i]))
        # 4. update forwarding graph (replace ns in and out)
        for fg in nsd.get("forwarding_graphs"):
            # add MP VNF to constituent VNF list
            fg.get("constituent_vnfs").append(mp.get("name"))
            # update forwarding paths
            for fp in fg.get("network_forwarding_paths"):
                # search and replace connection points specified in PED
                for fp_cp in fp.get("connection_points"):
                    if fp_cp.get("connection_point_ref") == mp_cp:
                        fp_cp["connection_point_ref"] = new_cp
            # update number of endpoints
            fg["number_of_endpoints"] -= 1
            LOG.debug("Updated forwarding graph '{}': {}"
                      .format(fg.get("fg_id"), fg))
        # 5. store updated nsd
        write_yaml(self._get_nsd_path(ec), nsd)
        # 6. log
        LOG.debug("Added measurement point VNF '{}' to NDS '{}'"
                  .format(mp.get("name"), nsd.get("name")))

    def _get_nsd_path(self, ec):
        """
        Returns path of NSD for given EC project.
        """
        projd = read_yaml(os.path.join(ec.project_path, "project.yml"))
        for f in projd.get("files"):
            # always use the first NSD we find (TODO improve)
            if f.get("type") == "application/vnd.5gtango.nsd":
                return os.path.join(ec.project_path, f.get("path"))
        raise BaseException(
            "No NSD found in project {}".format(projd.get("name")))
