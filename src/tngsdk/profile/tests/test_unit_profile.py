#  Copyright (c) 2017 SONATA-NFV, Paderborn University
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
# Neither the name of the SONATA-NFV, Paderborn University, UBIWHERE
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).

import os
import unittest
import tempfile
from son.profile.helper import compute_cartesian_product
from son.profile.profile import ProfileManager, parse_args
from son.profile.generator.sonata import SonataServiceConfigurationGenerator
from son.workspace.workspace import Workspace


# get path to our test files
TEST_PED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "misc/unittest_ped1.yml")
TEST_SON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "misc/sonata-fw-vtc-service.son")
TEST_WORK_DIR = tempfile.mkdtemp()


class UnitProfileTests(unittest.TestCase):

    def test_load_and_validate_ped(self):
        """
        Test reading and validation of test PED file.
        """
        args = parse_args(["-p", TEST_PED_FILE, "-v", "--mode", "active"])
        p = ProfileManager(args)
        # laod
        ped = p._load_ped_file(p.args.ped)
        # validate
        p._validate_ped_file(ped)
        # test ped contents
        self.assertEqual(len(ped.get("service_experiments")), 1)
        self.assertEqual(len(ped.get("function_experiments")), 2)
        self.assertEqual(len(ped), 10)

    def test_generate_experiment_specifications(self):
        """
        Test the generation of the experiment specifications
        based on the test PED file.
        """
        args = parse_args(["-p", TEST_PED_FILE, "-v", "--mode", "active"])
        p = ProfileManager(args)
        ped = p._load_ped_file(p.args.ped)
        # trigger generation
        se, fe = p._generate_experiment_specifications(ped)
        # test number of generated experiments
        self.assertEqual(len(se), 1)
        self.assertEqual(len(fe), 2)
        # test number of generated configurations
        self.assertEqual(len(se[0].experiment_configurations), 16)
        self.assertEqual(len(fe[0].experiment_configurations), 6)
        self.assertEqual(len(fe[1].experiment_configurations), 2)
        # test contents of the experiment configurations
        for ex in (se + fe):
            for c in ex.experiment_configurations:
                self.assertIn("measurement_point:mp.input:container", c.parameter)
                self.assertIn("measurement_point:mp.output:container", c.parameter)
                if ex.name != "func_vtc_throughput":
                    self.assertIn("resource_limitation:eu.sonata-nfv.fw-vnf.0.1:mem_swap_max", c.parameter)
                    self.assertIn("resource_limitation:eu.sonata-nfv.fw-vnf.0.1:mem_max", c.parameter)
                    self.assertIn("resource_limitation:eu.sonata-nfv.fw-vnf.0.1:cpu_cores", c.parameter)
                    self.assertIn("resource_limitation:eu.sonata-nfv.fw-vnf.0.1:io_bw", c.parameter)
                    self.assertIn("resource_limitation:eu.sonata-nfv.fw-vnf.0.1:cpu_bw", c.parameter)
                if ex.name != "func_fw_throughput":
                    self.assertIn("resource_limitation:eu.sonata-nfv.vtc-vnf.0.1:cpu_bw", c.parameter)
                    self.assertIn("resource_limitation:eu.sonata-nfv.vtc-vnf.0.1:mem_max", c.parameter)
                    self.assertIn("resource_limitation:eu.sonata-nfv.vtc-vnf.0.1:io_bw", c.parameter)
                    self.assertIn("resource_limitation:eu.sonata-nfv.vtc-vnf.0.1:cpu_cores", c.parameter)
                    self.assertIn("resource_limitation:eu.sonata-nfv.vtc-vnf.0.1:mem_swap_max", c.parameter)
                self.assertIn("resource_limitation:mp.output:cpu_bw", c.parameter)
                self.assertIn("measurement_point:mp.input:cmd_start", c.parameter)
                self.assertIn("resource_limitation:mp.output:mem_swap_max", c.parameter)
                self.assertIn("resource_limitation:mp.output:io_bw", c.parameter)
                self.assertIn("resource_limitation:mp.output:mem_max", c.parameter)
                self.assertIn("resource_limitation:mp.input:cpu_bw", c.parameter)
                self.assertIn("resource_limitation:mp.output:cpu_cores", c.parameter)
                self.assertIn("resource_limitation:mp.input:io_bw", c.parameter)
                self.assertIn("measurement_point:mp.input:cmd_stop", c.parameter)
                self.assertIn("measurement_point:mp.output:cmd_start", c.parameter)
                self.assertIn("resource_limitation:mp.input:mem_swap_max", c.parameter)
                self.assertIn("resource_limitation:mp.input:mem_max", c.parameter)
                self.assertIn("measurement_point:mp.output:cmd_stop", c.parameter)
                self.assertIn("resource_limitation:mp.input:cpu_cores", c.parameter)
                self.assertIn("repetition", c.parameter)


class UnitSonataGeneratorTests(unittest.TestCase):

    def setUp(self):
        """
        Creates a fresh test workspace in a temp dir to ensure
        we do not have conflicts with other CLI tests.
        """
        self.tmp_ws_dir = os.path.join(tempfile.mkdtemp(), "son-workspace")
        ws = Workspace(self.tmp_ws_dir, ws_name="son-profile test workspace")
        ws.create_dirs()
        ws.create_files()

    def test_load_and_extract(self):
        """
        Test extraction and loading of test *.son package and the contained
        service.
        """
        args = parse_args(["-p", TEST_PED_FILE, "-v", "--mode", "active"])
        # init generator
        sg = SonataServiceConfigurationGenerator(args)
        s = sg._load(TEST_SON_FILE, TEST_WORK_DIR)
        # tests
        self.assertEqual(len(s.manifest), 10)
        self.assertTrue(s.nsd is not None)
        self.assertEqual(len(s.vnfd_list), 2)
        self.assertTrue(s.metadata is not None)
        self.assertEqual(str(s), "SonataService(eu.sonata-nfv.package.sonata-fw-vtc-service.0.1)")
        self.assertTrue(os.path.exists(str(s.metadata.get("project_disk_path"))))
        self.assertFalse(os.path.exists(str(s.metadata.get("package_disk_path"))))
        
    def test_generate_function_experiments(self):
        """
        Test function experiment generation:
        - generated services
        - test NSD embedding
        - added measurement points
        - applied resource limits
        """
        # preparation
        args = parse_args(["-p", TEST_PED_FILE, "-v", "--mode", "active"])
        p = ProfileManager(args)
        ped = p._load_ped_file(p.args.ped)
        ses, fes = p._generate_experiment_specifications(ped)
        # init generator
        sg = SonataServiceConfigurationGenerator(args)
        base_service = sg._load(TEST_SON_FILE, TEST_WORK_DIR)
        # generate experiments
        gen = sg._generate_function_experiments(base_service, fes)
        # test generated data structures
        ## 1. test number of generated services, and result structure
        self.assertEqual(len(gen), 8)
        for k, v in gen.items():
            self.assertGreaterEqual(k, 0)
            self.assertGreaterEqual(v.metadata.get("run_id"), 0)
        ## 2. test embedding (based on template NSD)
        for k, v in gen.items():
            self.assertIsNotNone(v.nsd)
            self.assertEqual(v.nsd.get("name"), "son-profile-function-experiment")
            # check if all placeholders in template are replaced
            self.assertNotIn("{{", str(v.nsd))
            self.assertNotIn("}}", str(v.nsd))
        ## 3. test added measurement points
        for k, v in gen.items():
            self.assertIsNotNone(v.nsd)
            # check if MPs in function list
            has_input = False
            has_output = False
            for vnf in v.nsd.get("network_functions"):
                if vnf.get("vnf_name") == "mp.input":
                    has_input = True
                if vnf.get("vnf_name") == "mp.output":
                    has_output = True
            self.assertTrue(has_input)
            self.assertTrue(has_output)
            # check virtual links
            for vl in v.nsd.get("virtual_links"):
                cprs = vl.get("connection_points_reference")
                correct = False
                for c in cprs:
                    if "ns:mgmt" in c:
                        correct = True
                    if "mp.input:data" in c:
                        correct = True
                    if "mp.output:data" in c:
                        correct = True
                self.assertTrue(correct)
            # check forwarding graph
            for fg in v.nsd.get("forwarding_graphs"):
                self.assertIn("mp.input", fg.get("constituent_vnfs"))
                self.assertIn("mp.output", fg.get("constituent_vnfs"))
        ## 4. test resource limits
        for vnfd in v.vnfd_list:
            rl = vnfd.get("virtual_deployment_units")[0].get("resource_requirements")
            self.assertIsNotNone(rl)
            self.assertIn("cpu", rl)
            self.assertIn("memory", rl)
            self.assertIn("storage", rl)
            self.assertIn("cpu_bw", rl.get("cpu"))
            self.assertIn("vcpus", rl.get("cpu"))
            self.assertIn("size", rl.get("memory"))
            self.assertIn("size", rl.get("storage"))
            self.assertIsInstance(rl.get("cpu").get("cpu_bw"), float)
            self.assertIsInstance(rl.get("cpu").get("vcpus"), int)
            self.assertIsInstance(rl.get("memory").get("size"), int)
            self.assertIsInstance(rl.get("storage").get("size"), int)        

    def test_generate_service_experiments(self):
        """
        Test service experiment generation:
        - generated services
        - added measurement points
        - applied resource limits
        """
        # preparation
        args = parse_args(["-p", TEST_PED_FILE, "-v", "--mode", "active"])
        p = ProfileManager(args)
        ped = p._load_ped_file(p.args.ped)
        ses, fes = p._generate_experiment_specifications(ped)
        # init generator
        sg = SonataServiceConfigurationGenerator(args)
        base_service = sg._load(TEST_SON_FILE, TEST_WORK_DIR)
        # generate experiments
        gen = sg._generate_service_experiments(base_service, ses)
        # test generated data structures
        ## 1. test number of generated services, and result structure
        self.assertEqual(len(gen), 16)
        for k, v in gen.items():
            self.assertGreaterEqual(k, 0)
            self.assertGreaterEqual(v.metadata.get("run_id"), 0)
        ## 2. test added measurement points
        for k, v in gen.items():
            self.assertIsNotNone(v.nsd)
            # check if MPs in function list
            has_input = False
            has_output = False
            for vnf in v.nsd.get("network_functions"):
                if vnf.get("vnf_name") == "mp.input":
                    has_input = True
                if vnf.get("vnf_name") == "mp.output":
                    has_output = True
            self.assertTrue(has_input)
            self.assertTrue(has_output)
            # check virtual links
            has_input = False
            has_output = False
            for vl in v.nsd.get("virtual_links"):
                cprs = vl.get("connection_points_reference")   
                for c in cprs:
                    if "mp.input:data" in c:
                        has_input = True
                    if "mp.output:data" in c:
                        has_output = True
            self.assertTrue(has_input)
            self.assertTrue(has_output)
            # check forwarding graph
            for fg in v.nsd.get("forwarding_graphs"):
                self.assertIn("mp.input", fg.get("constituent_vnfs"))
                self.assertIn("mp.output", fg.get("constituent_vnfs"))
        ## 3. test resource limits
        for vnfd in v.vnfd_list:
            rl = vnfd.get("virtual_deployment_units")[0].get("resource_requirements")
            self.assertIsNotNone(rl)
            self.assertIn("cpu", rl)
            self.assertIn("memory", rl)
            self.assertIn("storage", rl)
            self.assertIn("cpu_bw", rl.get("cpu"))
            self.assertIn("vcpus", rl.get("cpu"))
            self.assertIn("size", rl.get("memory"))
            self.assertIn("size", rl.get("storage"))
            self.assertIsInstance(rl.get("cpu").get("cpu_bw"), float)
            self.assertIsInstance(rl.get("cpu").get("vcpus"), int)
            self.assertIsInstance(rl.get("memory").get("size"), int)
            self.assertIsInstance(rl.get("storage").get("size"), int)       

    def test_write_and_pack(self):
        """
        Test write-out and packaging of generated services.
        Checks if the *.son files are actually written
        to disk.
        """
        # preparation
        args = parse_args(["-p", TEST_PED_FILE, "-v", "--mode", "active"])
        p = ProfileManager(args)
        ped = p._load_ped_file(p.args.ped)
        ses, fes = p._generate_experiment_specifications(ped)
        # init generator
        sg = SonataServiceConfigurationGenerator(args)
        base_service = sg._load(TEST_SON_FILE, TEST_WORK_DIR)
        # generate experiments
        gen = dict()
        gen.update(sg._generate_function_experiments(base_service, fes))
        gen.update(sg._generate_service_experiments(base_service, ses))
        # do packaging
        res = sg._pack(TEST_WORK_DIR, gen, workspace_dir=self.tmp_ws_dir)
        # test if *.son files are generated
        for k, v in res.items():
            self.assertTrue(os.path.exists(v.get("sonfile")), msg="No generated package found.")
            self.assertIn("experiment_configuration", v)


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
