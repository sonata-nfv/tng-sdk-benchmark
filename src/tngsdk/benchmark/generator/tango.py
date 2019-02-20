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

import time
import shutil
import os
from tngsdk.benchmark.generator import ServiceConfigurationGenerator
from tngsdk.benchmark.helper import ensure_dir, read_yaml, write_yaml
from tngsdk.benchmark.helper import parse_ec_parameter_key
import tngsdk.package as tngpkg
from tngsdk.benchmark.logger import TangoLogger

LOG = TangoLogger.getLogger(__name__)


BASE_PKG_PATH = "base_pkg/"
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
        self.stat_n_ex = 0
        self.stat_n_ec = 0
        LOG.info("New 5GTANGO service configuration generator")
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
        # Step -1: Check if path exists
        if not os.path.exists(in_pkg_path):
            LOG.error("Could not load service referenced in PED: {}"
                      .format(in_pkg_path))
            exit(1)
        # Step 0 (optional): Support 5GTANGO projects
        if self._is_tango_project(in_pkg_path):
            # package the project first to temp
            r = self._pack(in_pkg_path, os.path.join(
                    self.args.work_dir, BASE_PKG_PATH))
            # re-write in_pkg_path
            in_pkg_path = r
        # Step 1: Unpack in_pkg to work_dir/BASE_PROJECT
        base_proj_path = os.path.join(
            self.args.work_dir, BASE_PROJECT_PATH)
        base_proj_path = self._unpack(in_pkg_path, base_proj_path)
        # Step 2: Generate for each experiment and package it
        for ex in service_ex:
            self._generate_projects(base_proj_path, ex)
            self.stat_n_ex += 1
        # Step 3: Return pointers to func_ex and service_ex
        return func_ex, service_ex

    def _unpack(self, pkg_path, proj_path):
        """
        Wraps the tng-sdk-package unpacking functionality.
        """
        args = [
            "--unpackage", pkg_path,
            "--output", proj_path,
            "--store-backend", "TangoProjectFilesystemBackend",
            "--format", "eu.5gtango",
            "--quiet",
            "--offline",
            "--loglevel"
        ]
        if self.args.verbose:
            args.append("info")
            # args.append("-v")
        else:
            args.append("error")
        if self.args.skip_validation:
            args.append("--skip-validation")
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
            "--format", "eu.5gtango",
            "--quiet",
            "--offline",
            "--loglevel"
        ]
        if self.args.verbose:
            args.append("info")
            # args.append("-v")
        else:
            args.append("error")
        if self.args.skip_validation:
            args.append("--skip-validation")
        # be sure that output dir is there
        ensure_dir(pkg_path)
        # call the package component
        LOG.debug("Calling package with args: {}".format(args))
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
            # 2. gather additional project infos
            self._gather_project_infos(ec)
            # 3. add MPs to project
            self._add_mps_to_project(ec)
            # 4. apply configuration parameters to project
            self._add_params_to_project(ec)
            # 5. package project
            self._package_project(ec)
            # 6. status output
            n_done += 1
            LOG.info("Generated project ({}/{}): {}"
                     .format(n_done,
                             len(ex.experiment_configurations),
                             os.path.basename(ec.package_path)))
        self.stat_n_ec += n_done

    def _copy_project(self, base_proj_path, ec):
        ec.project_path = os.path.join(
            self.args.work_dir, GEN_PROJECT_PATH, ec.name)
        LOG.debug("Created project: {}".format(ec.project_path))
        shutil.copytree(base_proj_path, ec.project_path)

    def _gather_project_infos(self, ec):
        """
        Collect additional infors about project and store to ec.
        e.g. mapping between VNF IDs and names
        """
        # VNF names to ID mapping based on NSD
        nsd = read_yaml(self._get_nsd_path(ec))
        for nf in nsd.get("network_functions"):
            k = "{}.{}.{}".format(nf.get("vnf_vendor"),
                                  nf.get("vnf_name"),
                                  nf.get("vnf_version"))
            ec.function_ids[k] = nf.get("vnf_id")

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
        # 1. read all VNFDs
        vnfds = self._read_vnfds(ec)
        # 2. update VNFDs
        for _, vnfd in vnfds.items():
            self._apply_parameters_to_vnfds(ec, vnfd)
        # 3. write updated VNFDs
        for path, vnfd in vnfds.items():
            write_yaml(path, vnfd)

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
        # add manually defined data interface address
        if mp.get("address"):
            for cp in vnfd["connection_points"]:
                if cp.get("id") == "data":
                    cp["address"] = mp.get("address")
            for vdu in vnfd["virtual_deployment_units"]:
                for cp in vdu["connection_points"]:
                    if cp.get("id") == "data":
                        cp["address"] = mp.get("address")
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
        # update links
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

    def _apply_parameters_to_vnfds(self, ec, vnfd):
        applied = False
        vnfd_uid = "{}.{}.{}".format(
            vnfd.get("vendor"), vnfd.get("name"), vnfd.get("version"))
        # iterate over all parameters to be applied
        for pname, pvalue in ec.parameter.items():
            ep_uid = parse_ec_parameter_key(pname).get("function_name")
            unit_name = parse_ec_parameter_key(pname).get("unit_name")
            field_name = parse_ec_parameter_key(pname).get("parameter_name")
            if ep_uid not in vnfd_uid:
                continue  # not the right VNFD -> skip
            # parameter should be applied to given VNF
            self._apply_parameter_to_vnfd(field_name, unit_name, pvalue, vnfd)
            applied = True
        if not applied:
            raise BaseException(
                "Couln't find any experiment parameters for VNFD: {}"
                .format(vnfd_uid))

    def _apply_parameter_to_vnfd(self, field_name, unit_name, value, vnfd):
        """
        Applies a single parameter (given by field name)
        to the given VNFD.
        """
        # Apply configuration to corresponding VNFD field
        # Two cases: VDU (unit_name) specified or not
        vdu = None
        if unit_name is None:  # use first VDU in VNFD
            vdu = vnfd.get(  # FIXME allow cloud native functions
                "virtual_deployment_units")[0]
        else:  # search for VDU to use
            # FIXME allow cloud native functions
            for u in vnfd.get("virtual_deployment_units"):
                if str(u.get("id")) == str(unit_name):
                    vdu = u
                    break
        if vdu is None:
            raise BaseException("Couldn't find deployment unit to manipulate.")
        # apply command fields (to non-MP VNFDs)
        if False:  # disabled (tng-bench directly injects commands for now)
            if field_name == "cmd_start" and "mp." not in vnfd.get("name"):
                # print("--- VNFD: {} --> cmd_start: {}"
                #       .format(vnfd.get("name"), value))
                vdu["vm_cmd_start"] = str(value)
            if field_name == "cmd_stop" and "mp." not in vnfd.get("name"):
                # print("--- VNFD: {} --> cmd_stop: {}"
                #       .format(vnfd.get("name"), value))
                vdu["vm_cmd_stop"] = str(value)
        # apply resource requirements
        rr = vdu.get("resource_requirements")
        # cpu cores
        if field_name == "cpu_cores":
            # cpu cores:
            # actually cpu_sets e.g. "1, 4, 12" to use 3 specific cores
            rr.get("cpu")["vcpus"] = (str(value)
                                      if value is not None else None)
        elif field_name == "cpu_bw":
            rr.get("cpu")["cpu_bw"] = (float(value)
                                       if value is not None else None)
        elif field_name == "mem_max":
            rr.get("memory")["size"] = (int(value)
                                        if value is not None else None)
            rr.get("memory")["size_unit"] = "MB"
        elif field_name == "disk_max":
            rr.get("storage")["size"] = int(value)
            rr.get("storage")["size_unit"] = "GB"
            # TODO extend this with io_bw etc?
        # LOG.debug("Updated '{}' in VNFD '{}' to: {}"
        #          .format(field_name, vnfd.get("name"), rr))

    def _get_nsd_path(self, ec):
        """
        Returns path of NSD for given EC project.
        """
        nsd_paths = self._get_paths_from_projectdescriptor(
            ec, "application/vnd.5gtango.nsd")
        if len(nsd_paths) > 0:
            # always use the first NSD we find (TODO improve)
            return nsd_paths[0]
        raise BaseException(
            "No NSD found for {}".format(ec.experiment))

    def _get_vnfd_paths(self, ec):
        """
        Returns paths of VNFDs for given EC project.
        """
        return self._get_paths_from_projectdescriptor(
            ec, "application/vnd.5gtango.vnfd")

    def _get_paths_from_projectdescriptor(self, ec, mime_type):
        """
        Get paths from project.yml for given mime_type.
        """
        projd = read_yaml(os.path.join(ec.project_path, "project.yml"))
        r = list()
        for f in projd.get("files"):
            if f.get("type") == mime_type:
                r.append(os.path.join(ec.project_path, f.get("path")))
        return r

    def _read_vnfds(self, ec):
        """
        Real all VNFDs from given project.
        Return {path, dict(vnfd)}.
        """
        r = dict()
        for p in self._get_vnfd_paths(ec):
            r[p] = read_yaml(p)
        return r

    def _is_tango_project(self, in_pkg_path):
        if not str(in_pkg_path).endswith(".tgo"):
            if (os.path.exists(
                os.path.join(in_pkg_path, "project.yml"))
                    or os.path.exists(
                        os.path.join(in_pkg_path, "project.yaml"))):
                return True
        return False

    def print_generation_and_packaging_statistics(self):
        print("-" * 80)
        print("5GTANGO tng-bench: Experiment generation report")
        print("-" * 80)
        print("Generated packages for {} experiments with {} configurations."
              .format(self.stat_n_ex, self.stat_n_ec))
        print("Total time: %s" % "%.4f" % (time.time() - self.start_time))
        print("-" * 80)
