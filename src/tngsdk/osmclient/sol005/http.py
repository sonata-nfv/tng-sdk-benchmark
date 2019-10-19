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

from io import BytesIO
import pycurl
import json
from osmclient.common import http

class Http(http.Http):

    def __init__(self, url, user='admin', password='admin'):
        self._url = url
        self._user = user
        self._password = password
        self._http_header = None

    def _get_curl_cmd(self, endpoint):
        curl_cmd = pycurl.Curl()
        #print self._url + endpoint
        curl_cmd.setopt(pycurl.URL, self._url + endpoint)
        curl_cmd.setopt(pycurl.SSL_VERIFYPEER, 0)
        curl_cmd.setopt(pycurl.SSL_VERIFYHOST, 0)
        if self._http_header:
            curl_cmd.setopt(pycurl.HTTPHEADER, self._http_header)
        return curl_cmd

    def delete_cmd(self, endpoint):
        data = BytesIO()
        curl_cmd = self._get_curl_cmd(endpoint)
        curl_cmd.setopt(pycurl.CUSTOMREQUEST, "DELETE")
        curl_cmd.setopt(pycurl.WRITEFUNCTION, data.write)
        curl_cmd.perform()
        http_code = curl_cmd.getinfo(pycurl.HTTP_CODE)
        #print 'HTTP_CODE: {}'.format(http_code)
        curl_cmd.close()
        # TODO 202 accepted should be returned somehow
        if data.getvalue():
            return http_code, data.getvalue().decode()
        else:
            return http_code, None

    def send_cmd(self, endpoint='', postfields_dict=None,
                 formfile=None, filename=None,
                 put_method=False, patch_method=False):
        data = BytesIO()
        curl_cmd = self._get_curl_cmd(endpoint)
        if put_method:
            curl_cmd.setopt(pycurl.CUSTOMREQUEST, "PUT")
        elif patch_method:
            curl_cmd.setopt(pycurl.CUSTOMREQUEST, "PATCH")
        curl_cmd.setopt(pycurl.POST, 1)
        curl_cmd.setopt(pycurl.WRITEFUNCTION, data.write)

        if postfields_dict is not None:
            jsondata = json.dumps(postfields_dict)
            curl_cmd.setopt(pycurl.POSTFIELDS, jsondata)
        elif formfile is not None:
            curl_cmd.setopt(
                pycurl.HTTPPOST,
                [((formfile[0],
                           (pycurl.FORM_FILE,
                            formfile[1])))])
        elif filename is not None:
            with open(filename, 'rb') as stream:
                postdata=stream.read()
            curl_cmd.setopt(pycurl.POSTFIELDS, postdata)

        curl_cmd.perform()
        http_code = curl_cmd.getinfo(pycurl.HTTP_CODE)
        curl_cmd.close()
        if data.getvalue():
            return http_code, data.getvalue().decode()
        else:
            return http_code, None

    def post_cmd(self, endpoint='', postfields_dict=None,
                 formfile=None, filename=None):
        return self.send_cmd(endpoint=endpoint,
                             postfields_dict=postfields_dict,
                             formfile=formfile,
                             filename=filename,
                             put_method=False, patch_method=False)

    def put_cmd(self, endpoint='', postfields_dict=None,
                formfile=None, filename=None):
        return self.send_cmd(endpoint=endpoint,
                             postfields_dict=postfields_dict,
                             formfile=formfile,
                             filename=filename,
                             put_method=True, patch_method=False)

    def patch_cmd(self, endpoint='', postfields_dict=None,
                formfile=None, filename=None):
        return self.send_cmd(endpoint=endpoint,
                             postfields_dict=postfields_dict,
                             formfile=formfile,
                             filename=filename,
                             put_method=False, patch_method=True)

    def get2_cmd(self, endpoint):
        data = BytesIO()
        curl_cmd = self._get_curl_cmd(endpoint)
        curl_cmd.setopt(pycurl.HTTPGET, 1)
        curl_cmd.setopt(pycurl.WRITEFUNCTION, data.write)
        curl_cmd.perform()
        http_code = curl_cmd.getinfo(pycurl.HTTP_CODE)
        curl_cmd.close()
        if data.getvalue():
            return http_code, data.getvalue().decode()
        return http_code, None

