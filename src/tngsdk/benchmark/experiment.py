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
from tngsdk.benchmark.macro import rewrite_parameter_macros_to_lists
from tngsdk.benchmark.helper import compute_cartesian_product

LOG = logging.getLogger(__name__)


class Experiment(object):

    def __init__(self, definition):
        self.resource_limitations = dict()
        self.profile_calculations = list()
        # populate object from YAML definition
        self.__dict__.update(definition)
        # attributes
        self.experiment_configurations = list()
        self.pre_configuration = dict()
        self.configuration_space_list = list()
        self.overload_vnf_list = list()
        # store original experiment definition for late use
        self.original_definition = definition.copy()

    def populate(self):
        """
        Search for parameter study macros and generate
        one run configuration for each parameter combination
        to be tested.
        """
        # convert parameter macros from PED file to plain lists
        for rl in self.resource_limitations:
            rewrite_parameter_macros_to_lists(rl)
        # convert measurment points from PED file to plain lists
        for mp in self.measurement_points:
            rewrite_parameter_macros_to_lists(mp)

        # IMEC
        # check for vnfs that need overload detection (imec mode)
        if hasattr(self, 'overload_detection'):
            for vnf_name in self.overload_detection:
                self.overload_vnf_list.append(vnf_name)
        # gather all configuration commands per VNF that
        # need to be executed once before all tests start
        self.pre_configuration = self._get_pre_configuration_as_dict()

        # UPB
        # generate a single flat dict containing all the
        # parameter study lists defined in the PED
        # this includes: header parameters (repetitions),
        # measurement point commands (all), and
        # function resource limitations
        configuration_dict = dict()
        configuration_dict.update(self._get_experiment_header_space_as_dict())
        configuration_dict.update(self._get_function_resource_space_as_dict())
        configuration_dict.update(self._get_mp_space_as_dict())
        LOG.debug("configuration space:{0}".format(configuration_dict))
        # explore entire parameter space by calculating the
        # Cartesian product over the given dict
        configuration_space_list = compute_cartesian_product(
            configuration_dict)
        self.configuration_space_list = configuration_space_list
        # create a experiment configuration objects for each calculated
        # configuration to test
        for c in configuration_space_list:
            rc = ExperimentConfiguration(self, c)
            self.experiment_configurations.append(rc)
        LOG.info("Populated experiment specification: {} with {} "
                 + "configurations to be executed."
                 .format(self.name, len(self.experiment_configurations)))

    def _get_pre_configuration_as_dict(self):
        """
        Create a dict that lists all commands that need to be executed per VNF,
        one-time execution as configuration before the tests start.
        :return: dict
        {"vnf_name1": [cmd1, cmd2, ...],
         "vnf_nameN": [cmd, ...],
        }
        """
        config_dict = dict()
        for mp in self.measurement_points:
            vnf_name = mp.get("name")
            vnf_config = mp.get("configuration")
            if vnf_config:
                if not isinstance(vnf_config, list):
                    vnf_config = [vnf_config]
                config_dict[vnf_name] = vnf_config

        LOG.debug('pre-configuration commands:{}'.format(config_dict))
        return config_dict

    def _get_experiment_header_space_as_dict(self):
        """
        {"repetition" : [0, 1, ...]}
        """
        r = dict()
        r["repetition"] = list(range(0, self.repetitions))
        return r

    def _get_function_resource_space_as_dict(self):
        """
        Create a flat dictionary with configuration lists to be tested
        # for each configuration parameter.
        Output: dict
        {"resource_limitation:funname1:parameter1" : [0.1, 0.2, ...],
         "resource_limitation:funname1:parameterN" : [0.1, ...],
         "resource_limitation:funname2:parameter1" : [0.1],
         "resource_limitation:funname2:parameterN" : [0.1, 0.2, ...],
        ... }
        """
        r = dict()
        for rl in self.resource_limitations:
            name = rl.get("function")
            for k, v in rl.items():
                if k == "function":
                    continue
                if not isinstance(v, list):
                    v = [v]
                r["resource_limitation:%s:%s" % (name, k)] = v
        return r

    def _get_mp_space_as_dict(self):
        """
        Create a flat dictionary with configuration lists to
        # be tested for each configuration parameter.
        Output: dict
        {"measurement_point:mpname1:parameter1" : [0.1, 0.2, ...],
         "measurement_point:mpname1:parameterN" : [0.1, ...],
         "measurement_point:mpname2:parameter1" : [0.1],
         "measurement_point:mpname2:parameterN" : [0.1, 0.2, ...],
         ...}
        """
        r = dict()
        for rl in self.measurement_points:
            name = rl.get("name")
            for k, v in rl.items():
                if (k == "name"
                        or k == "connection_point"
                        or k == "configuration"):  # skip some fields
                    continue
                if not isinstance(v, list):
                    v = [v]
                r["measurement_point:%s:%s" % (name, k)] = v
        return r


class ServiceExperiment(Experiment):

    def __init__(self, definition):
        super().__init__(definition)
        LOG.debug("Created service experiment specification %r" % self.name)


class FunctionExperiment(Experiment):

    def __init__(self, definition):
        super().__init__(definition)
        LOG.debug("Created function experiment specification: %r" % self.name)


class ExperimentConfiguration(object):
    """
    Holds the configuration parameters for a single experiment run.
    """
    # have globally unique run_ids for simplicity
    RUN_ID = 0

    def __init__(self, experiment, p):
        self.run_id = ExperimentConfiguration.RUN_ID
        ExperimentConfiguration.RUN_ID += 1
        self.name = experiment.name
        self.experiment = experiment
        self.parameter = p
        LOG.debug("Created: {}".format(self))

    def __repr__(self):
        return "ExperimentConfiguration({}_{})".format(self.name, self.run_id)
