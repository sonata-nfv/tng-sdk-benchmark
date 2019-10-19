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

"""
OSM package API handling
"""

from osmclient.common.exceptions import ClientException
from osmclient.common.exceptions import NotFound
from osmclient.common import utils


class Package(object):
    def __init__(self, http=None, upload_http=None, client=None):
        self._client = client
        self._http = http
        self._upload_http = upload_http

    def _wait_for_package(self, pkg_type):
        if 'vnfd' in pkg_type['type']:
            get_method = self._client.vnfd.get
        elif 'nsd' in pkg_type['type']:
            get_method = self._client.nsd.get
        else:
            raise ClientException("no valid package type found")

        # helper method to check if pkg exists
        def check_exists(func):
            try:
                func()
            except NotFound:
                return False
            return True

        return utils.wait_for_value(lambda:
                                    check_exists(lambda:
                                                 get_method(pkg_type['name'])))

    def get_key_val_from_pkg(self, descriptor_file):
        return utils.get_key_val_from_pkg(descriptor_file)

    def wait_for_upload(self, filename):
        """wait(block) for an upload to succeed.
           The filename passed is assumed to be a descriptor tarball.
        """
        pkg_type = utils.get_key_val_from_pkg(filename)

        if pkg_type is None:
            raise ClientException("Cannot determine package type")

        if not self._wait_for_package(pkg_type):
            raise ClientException("package {} failed to upload"
                                  .format(filename))

    def upload(self, filename):
        resp = self._upload_http.post_cmd(formfile=('package', filename))
        if not resp or 'transaction_id' not in resp:
            raise ClientException("failed to upload package")
