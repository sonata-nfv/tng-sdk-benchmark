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
import json
from pprint import pformat
from tngsdk.benchmark.macro import rewrite_parameter_macros_to_lists
from tngsdk.benchmark.helper import compute_cartesian_product
from tngsdk.benchmark.logger import TangoLogger


LOG = TangoLogger.getLogger(__name__)


DEFAULT_TIME_WARMUP = 10  # only used if not in PED


class Experiment(object):

    def __init__(self, args, definition, sut_package):
        self.name = None
        self.args = args
        self.sut_package = sut_package
        self.experiment_parameters = dict()
        self.measurement_points = list()
        self.repetitions = 0
        self.time_limit = 0
        self.time_warmup = DEFAULT_TIME_WARMUP
        # populate object from YAML definition
        self.__dict__.update(definition)
        # attributes
        self.experiment_configurations = list()
        self.configuration_space_list = list()
        # store original experiment definition for later use
        self.original_definition = definition.copy()

    def __repr__(self):
        return "Experiment({})".format(self.name)

    def populate(self):
        """
        Search for parameter study macros and generate
        one run configuration for each parameter combination
        to be tested.
        """
        # convert parameter macros from PED file to plain lists
        for ep in self.experiment_parameters:
            rewrite_parameter_macros_to_lists(ep)

        # generate a single flat dict containing all the
        # parameter study lists defined in the PED
        # this includes: header parameters (repetitions),
        # and experiment configurations parameters
        # (incl. resources and commands for functions)
        configuration_dict = dict()
        configuration_dict.update(
            self._get_header_configuration_space_as_dict())
        configuration_dict.update(
            self._get_mp_configuration_space_as_dict())
        configuration_dict.update(
            self._get_experiment_configuration_space_as_dict())
        LOG.debug("configuration space:{0}".format(configuration_dict))
        # explore entire parameter space by calculating the
        # Cartesian product over the given dict
        configuration_space_list = compute_cartesian_product(
            configuration_dict)
        self.configuration_space_list = self._add_config_ids(
            configuration_space_list)
        # create a experiment configuration objects for each calculated
        # configuration to test
        for c in configuration_space_list:
            rc = ExperimentConfiguration(self, c)
            self.experiment_configurations.append(rc)
        if self.args.max_experiments is not None:
            # reduce the number of experiments
            self.experiment_configurations = self.experiment_configurations[
                :int(self.args.max_experiments)]
        LOG.info("Populated experiment specification: '{}' with {} "
                 .format(self.name, len(self.experiment_configurations))
                 + "configurations to be executed.")

    def _add_config_ids(self, conf_list):
        """
        Add config_ids to the config list.
        Needs to be that complex, because we do not loop
        over the repetitions. So we have to diff the configs.
        Ugly, but works.
        """
        # count every different config (but ignore repetition field)
        cnt = 0
        cnt_dict = dict()
        for c in conf_list:
            tmpc = c.copy()
            del tmpc["ep::header::all::repetition"]
            k = json.dumps(tmpc, sort_keys=True)
            if k not in cnt_dict:
                cnt_dict[k] = cnt
                cnt += 1
        # add results to configs
        for c in conf_list:
            tmpc = c.copy()
            del tmpc["ep::header::all::repetition"]
            k = json.dumps(tmpc, sort_keys=True)
            c["ep::header::all::config_id"] = cnt_dict.get(k, 0)
        return conf_list

    def _get_header_configuration_space_as_dict(self):
        """
        {"repetition" : [0, 1, ...]}
        """
        r = dict()
        r["ep::header::all::repetition"] = list(range(0, self.repetitions))
        r["ep::header::all::time_limit"] = [self.time_limit]
        r["ep::header::all::time_warmup"] = [self.time_warmup]
        return r

    def _get_experiment_configuration_space_as_dict(self):
        """
        Create a flat dictionary with configuration lists to be tested
        for each experiment parameter.
        Output: dict
        {"ep::function::funname1::parameter1" : [0.1, 0.2, ...],
         "ep::function::funname1::parameterN" : ["ping", "iperf -s", ...],
         "ep::function::funname2::parameter1" : [0.1],
         "ep::function::funname2::parameterN" : ["ping", "iperf -s", ...],
        }
        """
        # generate flat dict:
        r = dict()
        for ep in self.experiment_parameters:
            ep_type, name = self._get_ep_type_name(ep)
            for k, v in ep.items():
                if k == ep_type:  # skip ep_type field
                    continue
                if not isinstance(v, list):
                    v = [v]
                r["ep::{}::{}::{}".format(ep_type, name, k)] = v
        return r

    def _get_mp_configuration_space_as_dict(self):
        """
        Create a flat dictionary with configuration lists to
        # be tested for each configuration parameter.
        Output: dict
        {"ep::mp::mpname1::parameter1" : [0.1, 0.2, ...],
         "ep::mp::mpname1::parameterN" : [0.1, ...],
         "ep::mp::mpname2::parameter1" : [0.1],
         "ep::mp::mpname2::parameterN" : [0.1, 0.2, ...],
         ...}
        """
        r = dict()
        for mp in self.measurement_points:
            name = mp.get("name")
            for k, v in mp.items():
                # if (k == "name"
                #        or k == "configuration"):  # skip some fields
                #    continue
                if not isinstance(v, list):
                    v = [v]
                r["ep::mp::%s::%s" % (name, k)] = v
        return r

    def _get_ep_type_name(self, ep):
        """
        Helper to get type and name of ep.
        Supportet types so far:
        - function
        - service
        """
        ep_type = None
        if "function" in ep:
            ep_type = "function"
        elif "service" in ep:
            ep_type = "service"
        if not ep_type:
            raise BaseException(
                "Couldn't parse 'experiment_parameter':{}"
                .format(ep))
        return ep_type, ep.get(ep_type)

    def get_function_ep_names(self, without=None):
        """
        Return list of function names that have experiment parameters
        assigned.
        """
        r = list()
        for ep in self.experiment_parameters:
            ep_type, name = self._get_ep_type_name(ep)
            if ep_type == "function":
                if without is None or without not in name:
                    r.append(name)
        return r


class OSMServiceExperiment(Experiment):

    def __init__(self, args, definition, sut_package):
        super().__init__(args, definition, sut_package)
        LOG.debug("Created service experiment specification %r" % self.name)


class OSMFunctionExperiment(Experiment):

    def __init__(self, args, definition, sut_package):
        super().__init__(args, definition, sut_package)
        LOG.debug("Created function experiment specification: %r" % self.name)


class ExperimentConfiguration(object):
    """
    Holds the configuration parameters for a single experiment run.
    Only these objects should be used by the package generators.
    """
    # have globally unique run_ids for simplicity
    RUN_ID = 0

    def __init__(self, experiment, p):
        self.experiment = experiment
        self.parameter = p
        self.run_id = ExperimentConfiguration.RUN_ID
        ExperimentConfiguration.RUN_ID += 1
        self.project_path = None  # path of generated project
        self.vnfd_package_path = None  # path of generated VNFD package
        self.nsd_package_path = None
        self.name = "{}_{:05d}".format(experiment.name, self.run_id)
        # additional information
        self.function_ids = dict()  # mapping between VNF names and IDs
        self.function_units = dict()  # mapping between VNF names and VDUs
        LOG.debug("Created: {}".format(self))

    def __repr__(self):
        return "ExperimentConfiguration({})".format(self.name)

    def pprint(self):
        return "{}\n{}".format(self, pformat(self.parameter))
