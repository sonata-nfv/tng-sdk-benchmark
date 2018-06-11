#  Copyright (c) 2015 SONATA-NFV, 5GTANGO, Paderborn University
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
import tempfile
import argparse
import logging
import coloredlogs
import time
from tngsdk.benchmark.experiment import ServiceExperiment, FunctionExperiment
from tngsdk.benchmark.helper import read_yaml
from tngsdk.benchmark.emulator import Emulator as Active_Emu_Profiler


LOG = logging.getLogger(os.path.basename(__file__))


def logging_setup():
    os.environ["COLOREDLOGS_LOG_FORMAT"] \
        = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"


class ProfileManager(object):
    """
    Main component class.
    """

    def __init__(self, args):
        self.start_time = time.time()
        self.service_experiments = list()
        self.function_experiments = list()
        self.generated_services = list()
        # arguments
        self.args = args
        self.args.ped = os.path.join(os.getcwd(), self.args.ped)
        self.work_dir = self.args.work_dir
        self.output_dir = self.args.output_dir
        # logging setup
        coloredlogs.install(level="DEBUG" if args.verbose else "INFO")
        LOG.info("SONATA profiling tool initialized")
        LOG.debug("Arguments: %r" % self.args)

    def run(self):
        """
        Run son-profile
        :return:
        """
        # try to load PED file
        self.ped = self._load_ped_file(self.args.ped)
        self._validate_ped_file(self.ped)
        # load and populate experiment specifications
        (self.service_experiments,
         self.function_experiments) = (
             self._generate_experiment_specifications(self.ped))

        if self.args.mode == "passive":
            print("NO passive mode")
            exit(1)
            # self._passive_execution()
        elif self.args.mode == "active":
            self._active_execution()

    def _active_execution(self):
        # generate service configuration using the specified generator module
        if not self.args.no_generation:
            # select and instantiate configuration generator
            cgen = None
            if self.args.service_generator == "sonata":
                from tngsdk.profile.generator.sonata \
                    import SonataServiceConfigurationGenerator
                cgen = SonataServiceConfigurationGenerator(self.args)
            else:
                LOG.error(
                    "Unknown service configuration generator specified: {0}"
                    .format(
                        self.args.service_generator))
                exit(1)
            if cgen is None:
                LOG.error("Service conf. generator instantiation failed.")
                exit(1)
            # generate one service configuration for each experiment based
            # on the service referenced in the PED file.
            gen_conf_list = cgen.generate(
                os.path.join(  # ensure that the reference is an absolute path
                    os.path.dirname(
                        self.ped.get("ped_path", "/")),
                    self.ped.get("service_package")),
                self.function_experiments,
                self.service_experiments,
                self.work_dir)
            LOG.debug("Generation result: {}".format(gen_conf_list))
            # display generator statistics
            if not self.args.no_display:
                cgen.print_generation_and_packaging_statistics()

        #
        # @Edmaas dict 'gen_conf_list' holds the generation data you need.
        #
        # Execute the generated packages
        if not self.args.no_execution:

            if not gen_conf_list:
                LOG.error("No generated packages, stopping execution")
                raise Exception(
                    "Cannot execute experiments: No generated packages")

            # get config file and read remote hosts description
            config_loc = self.args.config
            if not os.path.isabs(config_loc):
                config_loc = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        config_loc)
            remote_hosts = read_yaml(config_loc).get("target_platforms")

            # start the experiment series
            profiler = Active_Emu_Profiler(remote_hosts)
            profiler.do_experiment_series(gen_conf_list)

    @staticmethod
    def _load_ped_file(ped_path):
        """
        Loads the specified PED file.
        :param ped_path: path to file
        :return: dictionary
        """
        yml = None
        try:
            yml = read_yaml(ped_path)
            if yml is None:
                raise BaseException("PED file YAML error.")
        except BaseException:
            LOG.error("Couldn't load PED file %r. Abort." % ped_path)
            exit(1)
        # add path annotation to ped file (simpler
        # handling of referenced artifacts)
        yml["ped_path"] = ped_path
        LOG.info("Loaded PED file %r." % ped_path)
        return yml

    @staticmethod
    def _validate_ped_file(input_ped):
        """
        Semantic validation of PED file contents.
        Check for all things we need to have in PED file.
        :param input_ped: ped dictionary
        :return: None
        """
        try:
            if "service_package" not in input_ped:
                raise BaseException("No service_package field found.")
            # TODO extend this with PED fields that are REQUIRED
        except BaseException:
            LOG.exception("PED file verification error:")

    @staticmethod
    def _generate_experiment_specifications(input_ped):
        """
        Create experiment objects based on the contents of the PED file.
        :param input_ped: ped dictionary
        :return: service experiments list, function experiments list
        """
        service_experiments = list()
        function_experiments = list()

        # service experiments
        for e in input_ped.get("service_experiments", []):
            e_obj = ServiceExperiment(e)
            e_obj.populate()
            service_experiments.append(e_obj)

        # function experiments
        for e in input_ped.get("function_experiments", []):
            e_obj = FunctionExperiment(e)
            e_obj.populate()
            function_experiments.append(e_obj)

        return service_experiments, function_experiments


def parse_args(manual_args=None):
    """
    CLI interface definition.
    :return:
    TODO move to cli.py module
    """
    parser = argparse.ArgumentParser(
        description="Manage and control VNF and "
        + "service profiling experiments.")

    parser.add_argument(
        "-v",
        "--verbose",
        help="Increases logging level to debug.",
        required=False,
        default=False,
        dest="verbose",
        action="store_true")

    parser.add_argument(
        "-p",
        "--ped",
        help="PED file to be used for profiling run",
        required=True,
        dest="ped")

    parser.add_argument(
        "--work-dir",
        help="Dictionary for generated artifacts,"
        + " e.g., profiling packages. Will use a temporary"
        + " folder as default.",
        required=False,
        default=tempfile.mkdtemp(),
        dest="work_dir")

    parser.add_argument(
        "--output-dir",
        help="Folder to collect measurements. Default: Current directory.",
        required=False,
        default=os.getcwd(),
        dest="output_dir")

    parser.add_argument(
        "--no-generation",
        help="Skip profiling package generation step.",
        required=False,
        default=False,
        dest="no_generation",
        action="store_true")

    parser.add_argument(
        "--no-execution",
        help="Skip profiling execution step.",
        required=False,
        default=False,
        dest="no_execution",
        action="store_true")

    parser.add_argument(
        "--no-display",
        help="Disable realtime output of profiling results",
        required=False,
        default=False,
        dest="no_display",
        action="store_true")

    parser.add_argument(
        "--graph-only",
        help="only display graphs using the stored results",
        required=False,
        default=False,
        dest="graph_only",
        action="store_true")

    parser.add_argument(
        "-r",
        "--results_file",
        help="file to store the results",
        required=False,
        default="test_results.yml",
        dest="results_file")

    parser.add_argument(
        "--generator",
        help="Service configuration generator to be used. Default: 'sonata'",
        required=False,
        default="sonata",
        dest="service_generator")

    parser.add_argument(
        "--mode",
        help="Choose between active and passive execution. Default is passive",
        required=False,
        choices=["active", "passive"],
        default="passive",
        dest="mode")

    parser.add_argument(
        "-c",
        "--config",
        help="Son Profile config file. Default is config.yml. Path has to "
        + "either be absolute or relative to location of python script.",
        required=False,
        default="config.yml",
        dest="config")

    if manual_args is not None:
        return parser.parse_args(manual_args)
    return parser.parse_args()


def main():
    logging_setup()
    args = parse_args()
    # TODO better log configuration (e.g. file-based logging)
    if args.verbose:
        coloredlogs.install(level="DEBUG")
    else:
        coloredlogs.install(level="INFO")
    p = ProfileManager(args)
    p.run()
