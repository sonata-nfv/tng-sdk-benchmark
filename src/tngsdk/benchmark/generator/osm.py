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
import yaml
import tarfile
from io import BytesIO
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


class OSMServiceConfigurationGenerator(
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
        LOG.info("New OSM service configuration generator")
        LOG.debug("OSM generator args: {}".format(self.args))

    def generate(self, nsd_pkg_path, vnfd_pkg_path, func_ex, service_ex):
        """
        Generates service configurations according to the inputs.
        Returns a list of identifiers / paths to the
        generated service configurations.

        in_pkg_path is the directory that contains the ped and services folder
        """
        if func_ex is not None and len(func_ex):
            # function experiments are not considered
            LOG.warning("Function experiments are not supported!")
        self.start_time = time.time()
        LOG.info("Generating {} service experiments using {}"
                 .format(len(service_ex), nsd_pkg_path))
        # Step -1: Check if path exists
        if not os.path.exists(vnfd_pkg_path):
            LOG.error("Could not load vnfd package referenced in PED: {}"
                      .format(nsd_pkg_path))
            exit(1)
        if not os.path.exists(nsd_pkg_path):
            LOG.error("Could not load nsd package referenced in PED: {}"
                      .format(nsd_pkg_path))
            exit(1)

        # Step 1: decompress VNFD and NSD files
        original_vnfd_archive = tarfile.open(vnfd_pkg_path, 'r:gz')
        original_nsd_archive = tarfile.open(nsd_pkg_path, 'r:gz')

        # Step 2: Create enough file streams for VNFD

        output_vnfd_streams = []
        output_nsd_stream = None

        # Right now just one service experiment
        for ex_c in service_ex[0].experiment_configurations:
            filename_ext = f"{ex_c.name}_vnfd.tar.gz"
            file_path = os.path.join(self.args.work_dir, filename_ext)
            output_vnfd_streams.append(tarfile.open(file_path, "w:gz"))

        filename_ext = f"{service_ex[0].name}_nsd.tar.gz"
        file_path = os.path.join(self.args.work_dir, filename_ext)
        output_nsd_stream = tarfile.open(file_path, "w:gz")

        # Step 3: Create new VNFD files and update experiments

        for output_vnfd_pkg in output_vnfd_streams:
            self._update_output_vnfd_pkg(original_vnfd_archive, output_vnfd_pkg, service_ex[0],
                                         output_vnfd_streams.index(output_vnfd_pkg))

            # Close and write the contents of the file
            output_vnfd_pkg.close()

        # Step 4: Create new NSD file
        # To be implemented here
        self._update_output_nsd_pkg(original_nsd_archive, output_nsd_stream, service_ex[0])
        # Don't forget to then set service_ex.experiment_configurations.nsd_package_path variable
        return func_ex, service_ex

    def _update_output_vnfd_pkg(self, original_vnfd_archive, output_vnfd_pkg, service_ex, ec_index):
        """
        Updates the archive streams with data from the old archive
        """
        for pkg_file in original_vnfd_archive.getmembers():
            member_name = pkg_file.name
            if member_name.endswith(".yaml") or member_name.endswith(".yml"):
                member_contents = original_vnfd_archive.extractfile(pkg_file)
                vnfd_contents = yaml.safe_load(member_contents)

                self._configure_vnfd_params(vnfd_contents, service_ex, ec_index, output_vnfd_pkg)

                new_vnfd_ti = tarfile.TarInfo(member_name)
                new_vnfd_stream = yaml.dump(vnfd_contents).encode('utf8')
                new_vnfd_ti.size = len(new_vnfd_stream)
                buffer = BytesIO(new_vnfd_stream)
                output_vnfd_pkg.addfile(tarinfo=new_vnfd_ti, fileobj=buffer)
            else:
                output_vnfd_pkg.addfile(pkg_file, original_vnfd_archive.extractfile(pkg_file))

    def _configure_vnfd_params(self, vnfd_yaml, service_ex, ec_index, output_vnfd_pkg):
        """
        Update the YAML VNFD contents
        """
        vnfd_yaml['vnfd:vnfd-catalog']['vnfd'][0]['name']=service_ex.experiment_configurations[ec_index].name
        for pname, pvalue in service_ex.experiment_configurations[ec_index].parameter.items():
            function_type = parse_ec_parameter_key(pname).get("type")
            vnf_type = parse_ec_parameter_key(pname).get("function_name")
            field_name = parse_ec_parameter_key(pname).get("parameter_name")
            if function_type == "function" and 'mp.' not in vnf_type:
                if field_name == 'cpu_cores':
                    # Single VNFD single VDU for now
                    vnfd_yaml['vnfd:vnfd-catalog']['vnfd'][0]['vdu'][0]['vm-flavor']['vcpu-count'] = pvalue
                if field_name == 'mem_max':
                    # Single VNFD single VDU for now
                    vnfd_yaml['vnfd:vnfd-catalog']['vnfd'][0]['vdu'][0]['vm-flavor']['memory-mb'] = pvalue
            #else:
               # LOG.error("Unknown fields in vnfd params")
        service_ex.experiment_configurations[ec_index].vnfd_package_path = output_vnfd_pkg.name

    def _update_output_nsd_pkg(self, original_nsd_archive, output_nsd_stream, service_ex):
        """
        Updates the output_nsd_stream according to service_ex
        """
        for pkg_file in original_nsd_archive.getmembers():
            member_name = pkg_file.name
            if member_name.endswith(".yaml") or member_name.endswith(".yml"):
                member_contents = original_nsd_archive.extractfile(pkg_file)
                nsd_contents = yaml.safe_load(member_contents)

                self._add_probes_in_nsd(nsd_contents,service_ex)
                nsd_contents['nsd:nsd-catalog']['nsd'][0]['name']=service_ex.name

                new_nsd_ti = tarfile.TarInfo(member_name)
                new_nsd_stream = yaml.dump(nsd_contents).encode('utf8')
                new_nsd_ti.size = len(new_nsd_stream)
                buffer = BytesIO(new_nsd_stream)
                output_nsd_stream.addfile(tarinfo=new_nsd_ti, fileobj=buffer)
            else:
                output_nsd_stream.addfile(pkg_file, original_nsd_archive.extractfile(pkg_file))
        for ec_index in range(len(service_ex.experiment_configurations)):
            service_ex.experiment_configurations[ec_index].nsd_package_path = output_nsd_stream.name

    def _add_probes_in_nsd(self,nsd_contents,service_ex):
        """
        Updates the nsd file contents by adding probe configuration
        """
        constituent_vnfd = nsd_contents['nsd:nsd-catalog']['nsd'][0]['constituent-vnfd']
        max_idx = int(constituent_vnfd[0].get('member-vnf-index'))
        for cv in constituent_vnfd:
            if int(cv.get('member-vnf-index')) > max_idx:
                max_idx = int(cv.get('member-vnf-index'))
        for mp in service_ex.experiment_configurations[0].experiment.measurement_points:
            mp_name = mp.get('name')
            # get mp.vm-name->image #we dont need this as of now
            # Step 1 : Adding constituent vnfds for probes
            constituent_vnfd.append({"member-vnf-index":max_idx+1, "vnfd-id-ref":mp_name})
            # Step 2 : Adding probe vnfd connection point reference to vlds
            vld = nsd_contents['nsd:nsd-catalog']['nsd'][0]['vld']
            for vld_n in vld:
                if vld_n.get('vim-network-name')=='mgmt':
                    # Management Network
                    vnfd_connection_point_ref = vld_n.get('vnfd-connection-point-ref')
                    vnfd_connection_point_ref.append({'member-vnf-index-ref':max_idx+1, 'vnfd-connection-point-ref':'eth1-mgmt', 'vnfd-id-ref':mp_name})
                else:
                    # Data Network
                    vnfd_connection_point_ref = vld_n.get('vnfd-connection-point-ref')
                    vnfd_connection_point_ref.append({'member-vnf-index-ref':max_idx+1, 'vnfd-connection-point-ref':'eth0-data', 'vnfd-id-ref':mp_name})
            max_idx = max_idx+1

    def print_generation_and_packaging_statistics(self):
        print("-"*80)
        print("OSM tng-bench: Experiment generation report")
        print("-"*80)
        print("Generated OSM packages for {} experiments with {} configurations.".format(self.stat_n_ex,self.stat_n_ec))
        print("Total time: %s" % "%.4f" % (time.time() - self.start_time))
        print("-"*80)