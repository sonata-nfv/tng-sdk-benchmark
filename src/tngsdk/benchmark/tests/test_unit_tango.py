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
from tngsdk.benchmark.helper import read_yaml
from tngsdk.benchmark import ProfileManager, parse_args
from tngsdk.benchmark.generator.tango import TangoServiceConfigurationGenerator


# get path to our test files
TEST_PED_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "fixtures/unittest_ped1.yml")
TEST_TNG_PKG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "fixtures/5gtango-test-package.tgo")
TEST_WORK_DIR = tempfile.mkdtemp()


class UnitTangoGeneratorTests(unittest.TestCase):

    def setUp(self):
        pass

    def _generate_experiments_from_ped(self, args):
        """
        Mocks the input parts of the benchmarking tool
        and generates the experiments to be executed
        based on the given PED file.
        """
        p = ProfileManager(args)
        ped = p._load_ped_file(p.args.ped)
        ex, _ = p._generate_experiment_specifications(ped)
        return ex

    def test_unpack(self):
        """
        Test extraction and loading of test *.son package and the contained
        service.
        """
        args = parse_args(["-p", TEST_PED_FILE])
        print(args)
        # unpack
        g = TangoServiceConfigurationGenerator(args)
        pp = g._unpack(TEST_TNG_PKG, TEST_WORK_DIR)
        # test
        self.assertTrue(os.path.exists(pp))
        self.assertTrue(os.path.exists(
            os.path.join(pp, "project.yml")))

    def test_generate_projects(self):
        """
        Test the generation of experiment projects / packages using
        the give base package / project and test experiments.
        """
        args = parse_args(["-p", TEST_PED_FILE])
        # generate test experiments based on PED
        ex_list = self._generate_experiments_from_ped(args)
        self.assertEqual(1, len(ex_list))
        for ex in ex_list:
            self.assertEqual(64, len(ex.experiment_configurations))
        # run the generator with test experiments
        g = TangoServiceConfigurationGenerator(args)
        g.generate(TEST_TNG_PKG, None, ex_list)
        # check results
        # import pdb; pdb.set_trace()
        for ex in ex_list:
            for ec in ex.experiment_configurations:
                prj_p = ec.project_path
                self.assertTrue(os.path.exists(prj_p))
                self.assertIsNotNone(prj_p)
                # check generated project artifacts exist
                self.assertTrue(os.path.exists(
                    os.path.join(prj_p, "project.yml")))
                self.assertTrue(os.path.exists(
                    os.path.join(prj_p, "sources/Definitions/mynsd.yaml")))
                self.assertTrue(os.path.exists(
                    os.path.join(prj_p, "sources/Definitions/myvnfd.yaml")))
                self.assertTrue(os.path.exists(
                    os.path.join(prj_p, "mp.input.yaml")))
                self.assertTrue(os.path.exists(
                    os.path.join(prj_p, "mp.output.yaml")))
                # check MPs are in NSD
                nsd = read_yaml(
                    os.path.join(prj_p, "sources/Definitions/mynsd.yaml"))
                self.assertIn("mp.input",
                              [nf.get("vnf_name") for nf
                               in nsd.get("network_functions")])
                self.assertIn("mp.output",
                              [nf.get("vnf_name") for nf
                               in nsd.get("network_functions")])
                # TODO check correct forwarding path, CPs, and links
                # check config. params. of ec are in VNFD
                vnfd = read_yaml(
                    os.path.join(prj_p, "sources/Definitions/myvnfd.yaml"))
                rl = vnfd.get(
                    "virtual_deployment_units")[0].get(
                        "resource_requirements")
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
                # TODO check if values are the same as in ec
                # check generated package artifacts exist
                pkg_p = ec.package_path
                self.assertTrue(os.path.exists(pkg_p))
