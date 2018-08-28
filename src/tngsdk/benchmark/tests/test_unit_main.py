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


import os
import unittest
import tempfile
from tngsdk.benchmark.helper import compute_cartesian_product
from tngsdk.benchmark import ProfileManager, parse_args


# get path to our test files
TEST_PED_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "fixtures/unittest_ped1.yml")
TEST_TNG_PKG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "fixtures/5gtango-test-package.tgo")
TEST_WORK_DIR = tempfile.mkdtemp()


class UnitProfileTests(unittest.TestCase):

    def test_load_and_validate_ped(self):
        """
        Test reading and validation of test PED file.
        """
        args = parse_args(["-p", TEST_PED_FILE, "-v"])
        p = ProfileManager(args)
        # laod
        ped = p._load_ped_file(p.args.ped)
        # validate
        p._validate_ped_file(ped)
        # test ped contents
        self.assertEqual(len(ped.get("service_experiments")), 1)
        self.assertIsNone(ped.get("function_experiments"))
        self.assertEqual(len(ped), 9)

    def test_generate_experiment_specifications(self):
        """
        Test the generation of the experiment specifications
        based on the test PED file.
        """
        args = parse_args(["-p", TEST_PED_FILE, "-v"])
        p = ProfileManager(args)
        ped = p._load_ped_file(p.args.ped)
        # trigger generation
        se, fe = p._generate_experiment_specifications(ped)
        # test number of generated experiments
        self.assertEqual(len(se), 1)
        self.assertEqual(len(fe), 0)
        # test number of generated configurations
        self.assertEqual(len(se[0].experiment_configurations), 64)
        # self.assertEqual(len(fe[0].experiment_configurations), 6)
        # self.assertEqual(len(fe[1].experiment_configurations), 2)
        # test contents of the experiment configurations
        for ex in (se + fe):
            for c in ex.experiment_configurations:
                self.assertIn(
                    "mp::mp.input::container",
                    c.parameter)
                self.assertIn(
                    "mp::mp.output::container",
                    c.parameter)
                if ex.name != "func_vtc_throughput":
                    self.assertIn(
                        "rl::eu.5gtango.vnf1.0.1"
                        + "::mem_swap_max",
                        c.parameter)
                    self.assertIn(
                        "rl::eu.5gtango.vnf1.0.1"
                        + "::mem_max",
                        c.parameter)
                    self.assertIn(
                        "rl::eu.5gtango.vnf1.0.1"
                        + "::cpu_cores",
                        c.parameter)
                    self.assertIn(
                        "rl::eu.5gtango.vnf1.0.1::io_bw",
                        c.parameter)
                    self.assertIn(
                        "rl::eu.5gtango.vnf1.0.1::cpu_bw",
                        c.parameter)
                if ex.name != "func_fw_throughput":
                    self.assertIn(
                        "rl::eu.5gtango.vnf2.0.1::cpu_bw",
                        c.parameter)
                    self.assertIn(
                        "rl::eu.5gtango.vnf2.0.1"
                        + "::mem_max",
                        c.parameter)
                    self.assertIn(
                        "rl::eu.5gtango.vnf2.0.1::io_bw",
                        c.parameter)
                    self.assertIn(
                        "rl::eu.5gtango.vnf2.0.1"
                        + "::cpu_cores",
                        c.parameter)
                    self.assertIn(
                        "rl::eu.5gtango.vnf2.0.1"
                        + "::mem_swap_max",
                        c.parameter)
                self.assertIn(
                    "rl::mp.output::cpu_bw", c.parameter)
                self.assertIn(
                    "mp::mp.input::cmd_start", c.parameter)
                self.assertIn(
                    "rl::mp.output::mem_swap_max", c.parameter)
                self.assertIn(
                    "rl::mp.output::io_bw", c.parameter)
                self.assertIn(
                    "rl::mp.output::mem_max", c.parameter)
                self.assertIn(
                    "rl::mp.input::cpu_bw", c.parameter)
                self.assertIn(
                    "rl::mp.output::cpu_cores", c.parameter)
                self.assertIn(
                    "rl::mp.input::io_bw", c.parameter)
                self.assertIn(
                    "mp::mp.input::cmd_stop", c.parameter)
                self.assertIn(
                    "mp::mp.output::cmd_start", c.parameter)
                self.assertIn(
                    "rl::mp.input::mem_swap_max", c.parameter)
                self.assertIn(
                    "rl::mp.input::mem_max", c.parameter)
                self.assertIn(
                    "mp::mp.output::cmd_stop", c.parameter)
                self.assertIn(
                    "rl::mp.input::cpu_cores", c.parameter)
                self.assertIn(
                    "header::all::repetition", c.parameter)


class UnitHelperTests(unittest.TestCase):

    def test_cartesian_product(self):
        """
        Test the function which computes the cartesian product
        of a dictionary of lists.
        This one is used to explore the complete parameter space specifeid
        in a PED file.
        :return:
        """

        def _dict_is_in_list(d, l):
            for d1 in l:
                if d1 == d:
                    return True
            return False

        INPUT = {"x": [1, 2, 3], "y": ["value1", "value2"]}
        OUTPUT = [
            {"x": 1, "y": "value1"},
            {"x": 1, "y": "value2"},
            {"x": 2, "y": "value1"},
            {"x": 2, "y": "value2"},
            {"x": 3, "y": "value1"},
            {"x": 3, "y": "value2"}
        ]
        # calculate Cartesian product
        result = compute_cartesian_product(INPUT)
        # check if results are as expected
        self.assertEqual(len(result), len(OUTPUT))
        for d in result:
            self.assertTrue(_dict_is_in_list(d, OUTPUT))
