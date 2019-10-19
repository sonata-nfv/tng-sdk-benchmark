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

from io import BytesIO
import pycurl
import json


class Http(object):

    def __init__(self, url, user='admin', password='admin'):
        self._url = url
        self._user = user
        self._password = password
        self._http_header = None

    def set_http_header(self, header):
        self._http_header = header

    def _get_curl_cmd(self, endpoint):
        curl_cmd = pycurl.Curl()
        curl_cmd.setopt(pycurl.URL, self._url + endpoint)
        curl_cmd.setopt(pycurl.SSL_VERIFYPEER, 0)
        curl_cmd.setopt(pycurl.SSL_VERIFYHOST, 0)
        curl_cmd.setopt(
            pycurl.USERPWD,
            '{}:{}'.format(
                self._user,
                self._password))
        if self._http_header:
            curl_cmd.setopt(pycurl.HTTPHEADER, self._http_header)
        return curl_cmd

    def get_cmd(self, endpoint):

        data = BytesIO()
        curl_cmd = self._get_curl_cmd(endpoint)
        curl_cmd.setopt(pycurl.HTTPGET, 1)
        curl_cmd.setopt(pycurl.WRITEFUNCTION, data.write)
        curl_cmd.perform()
        curl_cmd.close()
        if data.getvalue():
            return json.loads(data.getvalue().decode())
        return None

    def delete_cmd(self, endpoint):
        data = BytesIO()
        curl_cmd = self._get_curl_cmd(endpoint)
        curl_cmd.setopt(pycurl.CUSTOMREQUEST, "DELETE")
        curl_cmd.setopt(pycurl.WRITEFUNCTION, data.write)
        curl_cmd.perform()
        curl_cmd.close()
        if data.getvalue():
            return json.loads(data.getvalue().decode())
        return None

    def post_cmd(self, endpoint='', postfields_dict=None, formfile=None, ):
        data = BytesIO()
        curl_cmd = self._get_curl_cmd(endpoint)
        curl_cmd.setopt(pycurl.POST, 1)
        curl_cmd.setopt(pycurl.WRITEFUNCTION, data.write)

        if postfields_dict is not None:
            jsondata = json.dumps(postfields_dict)
            curl_cmd.setopt(pycurl.POSTFIELDS, jsondata)

        if formfile is not None:
            curl_cmd.setopt(
                pycurl.HTTPPOST,
                [((formfile[0],
                           (pycurl.FORM_FILE,
                            formfile[1])))])

        curl_cmd.perform()
        curl_cmd.close()
        if data.getvalue():
            return json.loads(data.getvalue().decode())
        return None
