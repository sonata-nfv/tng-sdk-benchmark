# Copyright 2018 Telefonica
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

#from os import stat
#from os.path import basename
from osmclient.common.exceptions import ClientException
from osmclient.common.exceptions import NotFound
from osmclient.common import utils
import json


class Package(object):
    def __init__(self, http=None, client=None):
        self._client = client
        self._http = http

    def get_key_val_from_pkg(self, descriptor_file):
        return utils.get_key_val_from_pkg(descriptor_file)

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
        pkg_type = utils.get_key_val_from_pkg(filename)
        if pkg_type is None:
            raise ClientException("Cannot determine package type")
        if pkg_type['type'] == 'nsd':
            endpoint = '/nsd/v1/ns_descriptors_content'
        else:
            endpoint = '/vnfpkgm/v1/vnf_packages_content'
        #endpoint = '/nsds' if pkg_type['type'] == 'nsd' else '/vnfds'
        #print 'Endpoint: {}'.format(endpoint)
        headers = self._client._headers
        headers['Content-Type'] = 'application/gzip'
        #headers['Content-Type'] = 'application/binary'
        # Next three lines are to be removed in next version
        #headers['Content-Filename'] = basename(filename)
        #file_size = stat(filename).st_size
        #headers['Content-Range'] = 'bytes 0-{}/{}'.format(file_size - 1, file_size)
        headers["Content-File-MD5"] = utils.md5(filename)
        http_header = ['{}: {}'.format(key,val)
                      for (key,val) in list(headers.items())]
        self._http.set_http_header(http_header)
        http_code, resp = self._http.post_cmd(endpoint=endpoint, filename=filename)
        #print 'HTTP CODE: {}'.format(http_code)
        #print 'RESP: {}'.format(resp)
        if http_code in (200, 201, 202, 204):
            if resp:
                resp = json.loads(resp)
            if not resp or 'id' not in resp:
                raise ClientException('unexpected response from server - {}'.format(
                                      resp))
            print(resp['id'])
        else:
            msg = ""
            if resp:
                try:
                     msg = json.loads(resp)
                except ValueError:
                    msg = resp
            raise ClientException("failed to upload package - {}".format(msg))

