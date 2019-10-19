# Copyright 2017 Sandvine
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
from mock import Mock
from osmclient.v1 import package
from osmclient.common.exceptions import ClientException


class TestPackage(unittest.TestCase):

    def test_upload_fail(self):
        mock = Mock()
        mock.post_cmd.return_value = 'foo'
        self.assertRaises(ClientException,
                          package.Package(upload_http=mock).upload, 'bar')

        mock.post_cmd.return_value = None
        self.assertRaises(ClientException,
                          package.Package(upload_http=mock).upload, 'bar')

    def test_wait_for_upload_bad_file(self):
        mock = Mock()
        mock.post_cmd.return_value = 'foo'
        self.assertRaises(IOError,
                          package.Package(upload_http=mock).wait_for_upload,
                          'invalidfile')
