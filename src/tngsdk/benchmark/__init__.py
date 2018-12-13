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
from tngsdk.benchmark.generator.sonata \
                import SonataServiceConfigurationGenerator
from tngsdk.benchmark.generator.tango \
                import TangoServiceConfigurationGenerator
from tngsdk.benchmark.executor import Executor
from tngsdk.benchmark.helper import read_yaml
from tngsdk.benchmark.resultprocessor.ietfbmwg import IetfBmwgResultProcessor
from tngsdk.benchmark.logger import TangoLogger


logging.getLogger("urllib3").setLevel(logging.WARNING)


def setup_logging(args):
    """
    Configure logging.
    """
    log_level = logging.INFO
    # get loglevel from environment or --loglevel
    log_level_str = os.environ.get("LOGLEVEL", "INFO")
    if args.log_level:  # overwrite if present
        log_level_str = args.log_level
    # parse
    log_level_str = str(log_level_str).lower()
    if log_level_str == "debug":
        log_level = logging.DEBUG
    elif log_level_str == "info":
        log_level = logging.INFO
    elif log_level_str == "warning":
        log_level = logging.WARNING
    elif log_level_str == "error":
        log_level = logging.ERROR
    else:
        print("Loglevel '{}' unknown.".format(log_level_str))
    # if "-v" is there set to debug
    if args.verbose:
        log_level = logging.DEBUG
    # select logging mode
    log_json = os.environ.get("LOGJSON", args.logjson)
    # configure all TangoLoggers
    TangoLogger.reconfigure_all_tango_loggers(
        log_level=log_level, log_json=log_json)


class ProfileManager(object):
    """
    Main component class.
    """

    def __init__(self, args):
        self.logger = TangoLogger.getLogger(__name__)
        self.start_time = time.time()
        self.service_experiments = list()
        self.function_experiments = list()
        self.args = args
        self.args.debug = self.args.verbose
        self.args.ped = os.path.join(os.getcwd(), self.args.ped)
        self.args.config = self._load_config(os.path.abspath(args.configfile))
        # logging setup
        coloredlogs.install(level="DEBUG" if args.verbose else "INFO")
        self.logger.info("5GTANGO benchmarking/profiling tool initialized")
        self.logger.debug("Arguments: %r" % self.args)

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
        # trigger experiment execution
        self.cgen = self.load_generator()
        if self.cgen is None:
            return
        self.generate_experiments()
        self.execute_experiments()
        self.process_results()

    def load_generator(self):
        if self.args.no_generation:
            print("Skipping generation: --no-generation")
            return None
        # select and instantiate configuration generator
        cgen = None
        if self.args.service_generator == "sonata":
            cgen = SonataServiceConfigurationGenerator(self.args)
        if self.args.service_generator == "eu.5gtango":
            cgen = TangoServiceConfigurationGenerator(self.args)
        else:
            self.logger.error(
                "Unknown service configuration generator '{0}'. Exit 1."
                .format(self.args.service_generator))
            exit(1)
        if cgen is None:
            self.logger.error("Service conf. generator instantiation failed.")
            exit(1)
        return cgen

    def generate_experiments(self):
        if self.cgen is None:
            raise BaseException("No generator loaded.")
        # generate one service configuration for each experiment based
        # on the service referenced in the PED file.
        # outputs are annotated to
        # service_experiments.experiment.configurations
        #    .run_id
        #    .project_path
        #    .package_path
        self.cgen.generate(
            os.path.join(  # ensure that the reference is an absolute path
                 os.path.dirname(
                     self.ped.get("ped_path", "/")),
                 self.ped.get("service_package")),
            self.function_experiments,
            self.service_experiments)
        # display generator statistics
        if not self.args.no_display:
            self.cgen.print_generation_and_packaging_statistics()

    def execute_experiments(self):
        if self.args.no_execution:
            print("Skipping execution: --no-execution")
            return
        # create an executor
        exe = Executor(self.args, self.service_experiments)
        # prepare
        exe.setup()
        # run
        exe.run()
        # clean
        exe.teardown()

    def process_results(self):
        if self.args.no_result:
            self.logger.info("Skipping results: --no-result")
            return
        # create result prcessor
        rp_list = list()
        rp_list.append(IetfBmwgResultProcessor(
            self.args, self.service_experiments))
        self.logger.info("Prepared {} result processor(s)"
                         .format(len(rp_list)))
        # process results
        for rp in rp_list:
            self.logger.info("Running result processor '{}'". format(rp))
            rp.run()

    def _load_config(self, path):
        try:
            return read_yaml(path)
        except BaseException as ex:
            self.logger.error("Couldn't read config file: '{}'. Abort."
                              .format(path))
            self.logger.debug(ex)
            exit(1)

    def _load_ped_file(self, ped_path):
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
            self.logger.error("Couldn't load PED file %r. Abort." % ped_path)
            exit(1)
        # add path annotation to ped file (simpler
        # handling of referenced artifacts)
        yml["ped_path"] = ped_path
        self.logger.info("Loaded PED file %r." % ped_path)
        return yml

    def _validate_ped_file(self, input_ped):
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
            self.logger.exception("PED file verification error:")

    def _generate_experiment_specifications(self, input_ped):
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
        "--loglevel",
        help="Directly specify loglevel. Default: INFO",
        required=False,
        default=None,
        dest="log_level")

    parser.add_argument(
        "--logjson",
        help="Use 5GTANGO JSON-based logging. Default: False",
        required=False,
        default=False,
        dest="logjson",
        action="store_true")

    parser.add_argument(
        "-p",
        "--ped",
        help="PED file to be used for profiling run",
        required=True,
        dest="ped")

    parser.add_argument(
        "-c",
        "--config",
        help="Config file to be used, e.g., defining the execution platforms."
        + "Default: config.yml",
        required=False,
        default="config.yml",
        dest="configfile")

    parser.add_argument(
        "--work-dir",
        help="Dictionary for generated artifacts,"
        + " e.g., profiling packages. Will use a temporary"
        + " folder as default.",
        required=False,
        default=tempfile.mkdtemp(),
        dest="work_dir")

    parser.add_argument(
        "-rd",
        "--result-dir",
        help="Dictionary for measured results,"
        + " e.g., logfiles, monitoring data. Default: '(cwd)/results/'",
        required=False,
        default="results",
        dest="result_dir")

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
        "--no-result",
        help="Skip result processing step.",
        required=False,
        default=False,
        dest="no_result",
        action="store_true")

    parser.add_argument(
        "--hold",
        help=("Stop when experiment is started and" +
              " wait for user input (helps debugging)."),
        required=False,
        default=False,
        dest="hold_and_wait_for_user",
        action="store_true")

    parser.add_argument(
        "--no-display",
        help="Disable additional outputs.",
        required=False,
        default=False,
        dest="no_display",
        action="store_true")

    parser.add_argument(
        "--generator",
        help="Service configuration generator to be used."
        + " Default: 'eu.5gtango'",
        required=False,
        default="eu.5gtango",
        dest="service_generator")

    parser.add_argument(
        "--ibbd",
        help="Dictionary for generated IETF BMWG"
        + " 'benchmarking secriptors'."
        + " Default: None",
        required=False,
        default=None,
        dest="ibbd_dir")

    if manual_args is not None:
        return parser.parse_args(manual_args)
    return parser.parse_args()


def main(args=None):
    args = parse_args(args)
    setup_logging(args)
    p = ProfileManager(args)
    p.run()
