#  Copyright 2017 Sandvine
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import unittest
from osmclient.common import utils


class TestUtil(unittest.TestCase):

    def test_wait_for_method_basic(self):
        def foobar():
            return True
        assert utils.wait_for_value(lambda: foobar())

    def test_wait_for_method_timeout(self):
        def foobar():
            return False
        assert not utils.wait_for_value(lambda: foobar(), wait_time=0)

    def test_wait_for_method_paramter(self):
        def foobar(input):
            return input
        assert not utils.wait_for_value(lambda: foobar(False), wait_time=0)
        assert utils.wait_for_value(lambda: foobar(True), wait_time=0)

    def test_wait_for_method_wait_for_change(self):
        def foobar():
            if foobar.counter == 0:
                return True
            foobar.counter -= 1
            return False
        foobar.counter = 1
        assert utils.wait_for_value(lambda: foobar(), wait_time=1)

    def test_wait_for_method_exception(self):
        def foobar():
            raise Exception('send exception')
        assert not utils.wait_for_value(
            lambda: foobar(),
            wait_time=0,
            catch_exception=Exception)

    def test_wait_for_method_first_exception(self):
        def foobar():
            if foobar.counter == 0:
                return True
            foobar.counter -= 1
            raise Exception('send exception')
        foobar.counter = 1
        assert utils.wait_for_value(
            lambda: foobar(),
            wait_time=1,
            catch_exception=Exception)
