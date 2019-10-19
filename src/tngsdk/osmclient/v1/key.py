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
OSM ssh-key API handling
"""

import json
import pycurl
from io import BytesIO


class Key(object):

    def __init__(self, client=None):
        self._client = client

    def list(self):
        data = BytesIO()
        curl_cmd = self._client.get_curl_cmd('v1/api/config/key-pair?deep')
        curl_cmd.setopt(pycurl.HTTPGET, 1)
        curl_cmd.setopt(pycurl.WRITEFUNCTION, data.write)
        curl_cmd.perform()
        curl_cmd.close()
        resp = json.loads(data.getvalue().decode())
        if 'nsr:key-pair' in resp:
            return resp['nsr:key-pair']
        return list()
