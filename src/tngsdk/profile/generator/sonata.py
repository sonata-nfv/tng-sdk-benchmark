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
import zipfile
import os
import copy
import time
from termcolor import colored
from tabulate import tabulate
from tngsdk.profile.helper import read_yaml, write_yaml, relative_path, ensure_dir
from tngsdk.profile.generator import ServiceConfigurationGenerator
#from son.workspace.project import Project
#from son.workspace.workspace import Workspace
#from son.package.package import Packager


LOG = logging.getLogger(__name__)

# working directories created in "output_path"
SON_BASE_DIR = ".tmp_base_service"  # temp folder with input package contents
SON_GEN_SERVICES = ".tmp_gen_services"  # temp folder holding the unpacked generated services

class SonataServiceConfigurationGenerator(ServiceConfigurationGenerator):
    """
    SONATA Service Configuration Generator.
    Input: SONATA service package.
    Output: SONATA service packages.
    """

    def __init__(self, args):
        self.args = args
        self.RUN_ID = 0
        self.generated_services = dict()
        LOG.info("SONATA service configuration generator initialized")

    def generate(self, input_reference, function_experiments, service_experiments, working_path):
        """
        Generates service configurations according to the inputs.
        Returns a list of identifiers / paths to the generated service configurations.
        """
        self.start_time = time.time()
        self.output_path = working_path
        # load base service using PED reference (to a *.son file)
        base_service_obj = self._load(input_reference, working_path)
        # generate one SonataService for each experiment
        generated_service_objs = dict()
        generated_service_objs.update(self._generate_function_experiments(
            base_service_obj, function_experiments))
        generated_service_objs.update(self._generate_service_experiments(
            base_service_obj, service_experiments))
        # pack all generated services and write them to disk
        LOG.info("Starting to pack {} service configurations ...".format(len(generated_service_objs)))
        return self._pack(working_path, generated_service_objs)

    def _extract(self, input_reference, working_path):
        """
        Unzips a SONATA service package and stores all its contents
        to working_path + SON_BASE_DIR
        """
        # prepare working directory
        base_service_path = os.path.join(working_path, SON_BASE_DIR)
        ensure_dir(base_service_path)
        # locate referenced *.son file
        if not os.path.exists(input_reference):
            raise BaseException("Couldn't find referenced SONATA package: %r" % input_reference)
        # extract *.son file and put it into base_service_path
        LOG.debug("Unzipping: {} to {}".format(input_reference, base_service_path))
        with zipfile.ZipFile(input_reference, "r") as z:
            z.extractall(base_service_path)
        LOG.info("Extracted SONATA service package: {}".format(input_reference))
        return base_service_path

    def _load(self, input_reference, working_path):
        """
        Load a SONATA from the specified package (*.son).
        Creates temporary files in working_path.
        Returns SonataService objecct.
        """
        # extract service project from SONATA package
        base_service_path = self._extract(input_reference, working_path)
        return SonataService.load(base_service_path)

    def _generate_from_base_service(self, base_service_obj, ec):
        """
        Generates a new SonataService object based on given service using
        the given experiment configurations.
        """
        n = base_service_obj.copy()
        #n.manifest["name"] += "-{}".format(ec.run_id)
        n.metadata["run_id"] = ec.run_id
        n.metadata["exname"] = ec.name
        # lets store the entire experiment configuration for later use in the execution
        n.metadata["ec"] = {
            "parameter" : ec.parameter.copy(),
            "experiment" : ec.experiment.original_definition.copy()
        }
        LOG.debug("Created service from base: '{}' for experiment '{}' with run ID: {}".format(
            n.manifest["name"],
            n.metadata["exname"],
            n.metadata["run_id"]
        ))
        return n

    def _embed_function_into_experiment_nsd(
            self, service, ec,
            template="template/sonata_nsd_function_experiment.yml"):
        """
        Generates a NSD that contains the single VNF of the given
        function experiment and embeds the specified function into it.
        The new NSD overwrites the existing NSD in service.
        This unifies the follow up procedures for measurement point
        inclusion etc.
        The NSD template for this can be found in the template/ folder.
        """
        template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), template)
        new_nsd = read_yaml(template_path)
        # 1. update VNF section
        old_vnf_dict = None
        for vnf in service.nsd.get("network_functions"):
            if str(vnf.get("vnf_name")) in ec.experiment.function:
                old_vnf_dict = vnf
        if old_vnf_dict is None:
            LOG.error("Couldn't find function '{}' in service '{}'".format(
                ec.experiment.function,
                service
            ))
        new_vnf_dict = new_nsd.get("network_functions")[0]
        new_vnf_dict.update(old_vnf_dict)
        LOG.debug("Updated VNF section in '{}': {}".format(service, new_vnf_dict))
        # 1.5 remove obsolete VNFDs
        old_list = service.vnfd_list.copy()
        service.vnfd_list = list()
        for vnfd in old_list:
            if vnfd.get("name") == new_vnf_dict.get("vnf_name"):
                service.vnfd_list.append(vnfd)
        LOG.debug("Updated VNFD list in '{}': {}".format(service, service.vnfd_list))
        # 2. update virtual link section (get first three CPs from VNFD)
        # TODO remove order assumptions (current version is more a HACK!)
        vnfd = service.get_vnfd_by_uid(ec.experiment.function)
        new_link_list = new_nsd.get("virtual_links")
        cp_ids = [cp.get("id") for cp in vnfd.get("connection_points")]
        for i in range(0, min(len(new_link_list), len(cp_ids))):
            cpr = new_link_list[i]["connection_points_reference"]
            for j in range(0, len(cpr)):
                if "test_vnf" in cpr[j]:
                    cpr[j] = "{}:{}".format(new_vnf_dict.get("vnf_id"), cp_ids[i])
        LOG.debug("Updated VLink section in '{}': {}".format(service, new_link_list))
        # 3. update forwarding path section
        # TODO remove order assumptions (current version is more a HACK!)
        for fg in new_nsd.get("forwarding_graphs"):
            fg.get("constituent_vnfs")[0] = new_vnf_dict.get("vnf_id")
            for nfp in fg.get("network_forwarding_paths"):
                nfp_cp_list = nfp.get("connection_points")
                for i in range(1, min(len(nfp_cp_list), len(cp_ids))):
                    if "test_vnf" in nfp_cp_list[i].get("connection_point_ref"):
                        nfp_cp_list[i]["connection_point_ref"] = "{}:{}".format(new_vnf_dict.get("vnf_id"), cp_ids[i])
        LOG.debug("Updated forwarding graph section in '{}': {}".format(service, new_nsd.get("forwarding_graphs")))      
        # 4. replace NSD
        service.nsd = new_nsd

    def _add_measurement_points(self, service, ec):
        """
        Adds the measurement points specified in 'ec' to the given
        service object and interconnects them to the existing connection
        points, like specified in the PED.
        It basically replaces network service's external connection points
        with measurement VNFs.
        """
        for mp in ec.experiment.measurement_points:
            # generate VNFD
            vnfd = measurement_point_to_vnfd(mp, ec)
            # add VNFD to service object
            service.vnfd_list.append(vnfd)
            # add MP VNF to NSD
            service.nsd.get("network_functions").append({
                "vnf_id": mp.get("name"),
                "vnf_name": mp.get("name"),
                "vnf_vendor": "son-profile",
                "vnf_version": "1.0"
            })
            # connect measurement point to service (replace virt. links)
            mp_cp = mp.get("connection_point")
            new_cp = "{}:data".format(mp.get("name"))
            for vl in service.nsd.get("virtual_links"):
                cprs = vl.get("connection_points_reference")
                # replace ns in/out link endpoints in NSD
                for i in range(0, len(cprs)):
                    if cprs[i] == mp_cp:
                        cprs[i] = new_cp
                        LOG.debug(
                            "Replaced virtual link CPR '{}' by '{}'".format(mp_cp, cprs[i]))
            # update forwarding graph (replace ns in and out)
            for fg in service.nsd.get("forwarding_graphs"):
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
                LOG.debug("Updated forwarding graph '{}': {}".format(fg.get("fg_id"), fg))

            LOG.debug("Added measurement point VNF '{}' to '{}'".format(
                vnfd.get("name"),
                service
            ))

    def _apply_resource_limitations(self, service, ec):
        """
        Apply resource limitations to VNFDs of 'service'.
        VNFDs and parameter names are identified by the keys of
        the configuration dict to be used ('ec').
        """
        # for each resource_limit in ec.parameter
        # get function by id
        # update parameter in resource limitation section

        for rlk, rlv in ec.parameter.items():
            # only consider resource limit parameters
            if "resource_limitation" in rlk:
                # for each resource limit config find the corresponding VNFD in service
                vnf_uid, param_name = split_conf_parameter_key(rlk)
                vnfd = service.get_vnfd_by_uid(vnf_uid)
                if vnfd is None:
                    LOG.error("VNF '{}' not found in service '{}'. Skip.".format(
                        vnf_uid, service
                    ))
                    continue
                # apply configuration to corresponding VNFD field (we assume a single VDU!)
                rr = vnfd.get("virtual_deployment_units")[0].get("resource_requirements")
                # cpu cores
                if param_name == "cpu_cores":
                    rr.get("cpu")["vcpus"] = int(float(rlv))
                if param_name == "cpu_bw":
                    rr.get("cpu")["cpu_bw"] = float(rlv)
                if param_name == "mem_max":
                    rr.get("memory")["size"] = int(float(rlv))
                    rr.get("memory")["size_unit"] = "MB"
                if param_name == "disk_max":
                    rr.get("storage")["size"] = int(float(rlv))
                    rr.get("storage")["size_unit"] = "GB"
                # TODO extend this with io_bw etc?
                LOG.debug("Updated '{}' resource requirements '{}': {}".format(
                    param_name, vnf_uid, rr
                ))
        LOG.debug("Applied resource limitations to service '{}'".format(service))

    def _generate_function_experiments(self, base_service_obj, experiments):
        """
        Generate function experiments according to given experiment descriptions.
        Generated experiments are based on the given network service.
        A single function is extracted and embedded into a test service descriptor
        to test the function in isolation.
        return: dict<run_id, service_obj>
        """
        r = dict()
        for e in experiments:
            for ec in e.experiment_configurations:
                # generate new service obj from base_service_obj
                ns = self._generate_from_base_service(base_service_obj, ec)
                # embed function experiment into a test service
                self._embed_function_into_experiment_nsd(ns, ec)
                # replace original nsd with test nsd
                # add measurement points to service
                self._add_measurement_points(ns, ec)
                # apply resource limitations
                self._apply_resource_limitations(ns, ec)
                # add service to result data structure
                r[ec.run_id] = ns
                # INFO message
                LOG.info(
                    "Generated function experiment '{}': '{}' with run ID: {}".format(
                        e.name, ns, ec.run_id))
        return r

    def _generate_service_experiments(self, base_service_obj, experiments):
        """
        Generate service experiments according to given experiment descriptions.
        Generated experiments are based on the given network service.
        return: dict<run_id, service_obj>
        """
        r = dict()
        for e in experiments:
            for ec in e.experiment_configurations:
                # generate new service obj from base_service_obj
                ns = self._generate_from_base_service(base_service_obj, ec)
                # add measurement points to service
                self._add_measurement_points(ns, ec)
                # apply resource limitations
                self._apply_resource_limitations(ns, ec)
                # add service to result data structure
                r[ec.run_id] = ns
                # INFO message
                LOG.info(
                    "Generated service experiment '{}': '{}' with run ID: {}".format(
                        e.name, ns, ec.run_id))
        return r

    def _pack(self, output_path, service_objs, workspace_dir=Workspace.DEFAULT_WORKSPACE_DIR):
        """
        return: dict<run_id: package_path>
        """
        r = dict()
        for i, s in service_objs.items():
            r[i] = dict()
            r[i]["sonfile"] = s.pack(output_path, self.args.verbose, workspace_dir=workspace_dir)
            r[i]["experiment_configuration"] = s.metadata.get("ec")
            self.generated_services[i] = s  # keep a pointformat(len(r), output_path))
        return r

    def print_generation_and_packaging_statistics(self):

        def b(txt):
            return colored(txt, attrs=['bold'])

        def get_exname_list(slist):
            return set(s.metadata.get("exname") for s in slist)

        def get_services_by_exname(exname):
            return [s for s in self.generated_services.values() if s.metadata.get("exname") == exname]

        def get_pkg_time(l):
            return sum([s.metadata.get("package_generation_time") for s in l])

        def get_pkg_size(l):
            return sum([float(s.metadata.get("package_disk_size")) / 1024 for s in l])

        def generate_table():
            rows = list()
            # header
            rows.append([b("Experiment"), b("Num. Pkg."), b("Pkg. Time (s)"), b("Pkg. Sizes (kB)")])
            # body
            sum_pack_time = 0.0
            sum_file_size = 0.0
            for en in get_exname_list(self.generated_services.values()):
                filtered_s = get_services_by_exname(en)
                rows.append([en, len(filtered_s), get_pkg_time(filtered_s), get_pkg_size(filtered_s)])
                sum_pack_time += get_pkg_time(filtered_s)
                sum_file_size += get_pkg_size(filtered_s)
            # footer
            rows.append([b("Total"), b(len(self.generated_services)), b(sum_pack_time), b(sum_file_size)])
            return rows

        print(b("-" * 80))
        print(b("SONATA Profiler: Experiment Package Generation Report (sonata-pkg-gen)"))
        print(b("-" * 80))
        print("")
        print(tabulate(generate_table(), headers="firstrow", tablefmt="orgtbl"))
        print("")
        print("Generated service packages path: %s" % b(self.output_path))
        print("Total time: %s" % b("%.4f" % (time.time() - self.start_time)))
        print("")


class SonataService(object):
    """
    Represents a SONATA network service project.
    Contains NSD and multiple VNFDs and offers methods to store
    the network service project and to package it.
    """

    def __init__(self, manifest, nsd, vnfd_list, metadata):
        self.manifest = manifest
        self.nsd = nsd
        self.vnfd_list = vnfd_list
        self.metadata = self._init_metadata()
        self.metadata.update(metadata)
        LOG.debug("Initialized: {}".format(self))


    def __repr__(self):
        return "SonataService({}.{}.{})".format(
            self.manifest.get("vendor"),
            self.manifest.get("name"),
            self.manifest.get("version"))

    @staticmethod
    def _init_metadata():
        m = dict()
        m["run_id"] = -1
        m["exname"] = None
        m["project_disk_path"] = None
        m["package_disk_path"] = None
        return m

    @staticmethod
    def load(path):
        """
        Loads the service package contents from the given path.
        :param path: path to a folder with service package contents.
        :return: SonataService object.
        """
        # load manifest
        manifest = read_yaml(
            os.path.join(path, "META-INF/MANIFEST.MF"))
        # load nsd
        nsd = read_yaml(
            os.path.join(
                path,
                relative_path(manifest.get("entry_service_template"))))
        # load vnfds
        vnfd_list = list()
        for ctx in manifest.get("package_content"):
            if "function_descriptor" in ctx.get("content-type"):
                vnfd_list.append(
                    read_yaml(
                        os.path.join(path,
                                     relative_path(ctx.get("name")))))
        # add some meta information
        metadata = dict()
        metadata["project_disk_path"] = path
        # create SonataServicePackage object
        s = SonataService(manifest, nsd, vnfd_list, metadata)
        LOG.info(
            "Loaded SONATA service package contents: {} ({} VNFDs).".format(
                s,
                len(vnfd_list)))
        # create SonataServicePackage object
        return s

    @property
    def pd(self):
        """
        Generate project descriptor based on information form
        the manifest file of the base package.
        """
        d = dict()
        d["descriptor_extension"] = "yml"
        d["version"] = "0.5"
        p = dict()
        p["description"] = self.manifest.get("description")
        p["maintainer"] = self.manifest.get("maintainer")
        p["name"] = self.manifest.get("name")
        p["vendor"] = self.manifest.get("vendor")
        p["version"] = self.manifest.get("version")
        d["package"] = p
        return d

    @property
    def pkg_name(self):
        """
        Generate name used for generated service project folder and package.
        :return: string
        """
        return "%s_%05d" % (self.metadata.get("exname"), self.metadata.get("run_id"))

    def copy(self):
        """
        Create a real copy of this service object.
        :return: object
        """
        LOG.debug("Copy: {}".format(self))
        return copy.deepcopy(self)

    def _write(self, output_path):
        """
        Write this SONATA service project structure to disk. This includes
        all descriptors etc. The generated files can be used as input to
        the SONATA packaging tool.
        """
        path = os.path.join(output_path, SON_GEN_SERVICES, self.pkg_name)
        # update package path to reflect new location
        self.metadata["project_disk_path"] = path
        # create output folder
        ensure_dir(path)
        # write project yml
        write_yaml(os.path.join(path, "project.yml"), self.pd)
        # write nsd
        nsd_dir = os.path.join(path, "sources/nsd")
        ensure_dir(nsd_dir)
        write_yaml(os.path.join(nsd_dir,  "%s.yml" % self.nsd.get("name")), self.nsd)
        # write all vnfds
        vnf_dir = os.path.join(path, "sources/vnf")
        for vnfd in self.vnfd_list:
            d = os.path.join(vnf_dir, vnfd.get("name"))
            ensure_dir(d)
            write_yaml(os.path.join(d, "%s.yml" % vnfd.get("name")), vnfd)
        LOG.debug("Wrote: {} to {}".format(self, path))
        return path
    
    def pack(self, output_path, verbose=False, workspace_dir=Workspace.DEFAULT_WORKSPACE_DIR):
        """
        Creates a *.son file of this service object.
        First writes the normal project structure to disk (to be used with packaging tool)
        """
        start_time = time.time()
        tmp_path = self._write(output_path)
        pkg_path = os.path.join(output_path, self.pkg_name) + ".son"
        LOG.warning(pkg_path)
        self.metadata["package_disk_path"] = pkg_path
        # be sure the target directory exists
        ensure_dir(output_path)
        # obtain workspace
        # TODO have workspace dir as command line argument
        workspace = Workspace.__create_from_descriptor__(workspace_dir)
        if workspace is None:
            LOG.error("Couldn't initialize workspace: %r. Abort." % workspace_dir)
            exit(1)
        # force verbosity of external tools if required
        workspace.log_level = "DEBUG" if verbose else "INFO"
        # obtain project
        project = Project.__create_from_descriptor__(workspace, tmp_path)
        if project is None:
            LOG.error("Packager couldn't load service project: %r. Abort." % tmp_path)
            exit(1)
        # initialize and run packager
        pck = Packager(workspace, project, dst_path=output_path)
        pck.generate_package(self.pkg_name)
        self.metadata["package_disk_size"] = os.path.getsize(pkg_path)
        self.metadata["package_generation_time"] = time.time() - start_time
        LOG.debug("Packed: {} to {}".format(self, pkg_path))
        return pkg_path

    def get_vnfd_by_uid(self, vnf_uid):
        """
        Fuzzy find VNFD by either:
        - vnf_uid == name
        - vnf_uid == vandor.name.version
        return vnfd
        """
        for vnfd in self.vnfd_list:
            if vnfd.get("name") == vnf_uid:
                return vnfd
            elif "{}.{}.{}".format(
                    vnfd.get("vendor"), vnfd.get("name"), vnfd.get("version")
            ) == vnf_uid:
                return vnfd
        return None

###
### Helper
###

def measurement_point_to_vnfd(mp, ec, template="template/sonata_vnfd_mp.yml"):
    """
    Generates a VNFD data structure using measurement point information
    from a PED file. VNFD is based on given template.
    """
    template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), template)
    vnfd = read_yaml(template_path)
    # replace placeholder fields (this highly depends on used template!)
    vnfd["name"] = mp.get("name")
    # allow different containers as parameter study
    vnfd["virtual_deployment_units"][0]["vm_image"] = ec.parameter.get(
        "measurement_point:{}:container".format(mp.get("name")))
    return vnfd


def split_conf_parameter_key(rlk):
    """
    Splits key of configuration parameter dict.
    return function_uid, parameter_name
    """
    try:
        p = rlk.split(":")
        return p[1], p[2]
    except:
        LOG.error("Couldn't parse configuration parameter key.")
    return None, None
