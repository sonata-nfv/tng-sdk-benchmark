# Copyright 2019 Whitestack, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact: esousa@whitestack.com or glavado@whitestack.com
##

"""
OSM role mgmt API
"""

from osmclient.common import utils
from osmclient.common.exceptions import ClientException
from osmclient.common.exceptions import NotFound
import json
import yaml


class Role(object):
    def __init__(self, http=None, client=None):
        self._http = http
        self._client = client
        self._apiName = '/admin'
        self._apiVersion = '/v1'
        self._apiResource = '/roles'
        self._apiBase = '{}{}{}'.format(self._apiName,
                                        self._apiVersion, self._apiResource)

    def create(self, name, permissions):
        """
        Creates a new OSM role.

        :param name: name of the role.
        :param permissions: permissions of the role in YAML.
        :raises ClientException: when receives an unexpected from the server.
        :raises ClientException: when fails creating a role.
        """
        role = {"name": name}

        if permissions:
            role_permissions = yaml.load(permissions)

            if not isinstance(role_permissions, dict):
                raise ClientException('Role permissions should be provided in a key-value fashion')

            for key, value in role_permissions.items():
                if not isinstance(value, bool):
                    raise ClientException("Value of '{}' in a role permissions should be boolean".format(key))

            role["permissions"] = role_permissions

        http_code, resp = self._http.post_cmd(endpoint=self._apiBase,
                                              postfields_dict=role)
        # print('HTTP CODE: {}'.format(http_code))
        # print('RESP: {}'.format(resp))
        if http_code in (200, 201, 202, 204):
            if resp:
                resp = json.loads(resp)
            if not resp or 'id' not in resp:
                raise ClientException('Unexpected response from server - {}'.format(
                                      resp))
            print(resp['id'])
        else:
            msg = ""
            if resp:
                try:
                    msg = json.loads(resp)
                except ValueError:
                    msg = resp
            raise ClientException("Failed to create role {} - {}".format(name, msg))

    def update(self, name, new_name, permissions, add=None, remove=None):
        """
        Updates an OSM role identified by name.

        NOTE: definition and add/remove are mutually exclusive.

        :param name: name of the role
        :param set_name: if provided, change the name.
        :param permissions: if provided, overwrites the existing role specification.  NOT IMPLEMENTED
        :param add: if provided, adds new rules to the definition.
        :param remove: if provided, removes rules from the definition.
        :raises ClientException: when receives an unexpected response from the server.
        :raises ClientException: when fails updating a role.
        """
        if new_name is None and permissions is None and add is None and remove is None:
            raise ClientException('At least one option should be provided')
        elif permissions and (add or remove):
            raise ClientException('permissions and add/remove are mutually exclusive')

        role_obj = self.get(name)
        new_role_obj = {"permissions": {}}
        if new_name:
            new_role_obj["name"] = new_name

        if permissions:
            role_definition = yaml.load(permissions)

            if not isinstance(role_definition, dict):
                raise ClientException('Role permissions should be provided in a key-value fashion')

            for key, value in role_definition.items():
                if not isinstance(value, bool) and value is not None:
                    raise ClientException('Value in a role permissions should be boolean or None to remove')

            new_role_obj["permissions"] = role_definition
        else:
            if remove:
                keys_from_remove = yaml.load(remove)

                if not isinstance(keys_from_remove, list):
                    raise ClientException('Keys should be provided in a list fashion')

                for key in keys_from_remove:
                    if not isinstance(key, str):
                        raise ClientException('Individual keys should be strings')
                    new_role_obj["permissions"][key] = None

            if add:
                add_roles = yaml.load(add)

                if not isinstance(add_roles, dict):
                    raise ClientException('Add should be provided in a key-value fashion')

                for key, value in add_roles.items():
                    if not isinstance(value, bool):
                        raise ClientException("Value '{}' in a role permissions should be boolean".format(key))

                    new_role_obj["permissions"][key] = value
        if not new_role_obj["permissions"]:
            del new_role_obj["permissions"]

        http_code, resp = self._http.put_cmd(endpoint='{}/{}'.format(self._apiBase, role_obj['_id']),
                                             postfields_dict=new_role_obj)
        # print('HTTP CODE: {}'.format(http_code))
        # print('RESP: {}'.format(resp))
        if http_code in (200, 201, 202):
            if resp:
                resp = json.loads(resp)
            if not resp or 'id' not in resp:
                raise ClientException('Unexpected response from server - {}'.format(
                                      resp))
            print(resp['id'])
        elif http_code == 204:
            print("Updated")
        else:
            msg = ""
            if resp:
                try:
                    msg = json.loads(resp)
                except ValueError:
                    msg = resp
            raise ClientException("Failed to update role {} - {}".format(name, msg))

    def delete(self, name, force=False):
        """
        Deletes an OSM role identified by name.

        :param name:
        :param force:
        :raises ClientException: when fails to delete a role.
        """
        role = self.get(name)
        querystring = ''
        if force:
            querystring = '?FORCE=True'
        http_code, resp = self._http.delete_cmd('{}/{}{}'.format(self._apiBase,
                                                                 role['_id'], querystring))
        # print('HTTP CODE: {}'.format(http_code))
        # print('RESP: {}'.format(resp))
        if http_code == 202:
            print('Deletion in progress')
        elif http_code == 204:
            print('Deleted')
        elif resp and 'result' in resp:
            print('Deleted')
        else:
            msg = ""
            if resp:
                try:
                    msg = json.loads(resp)
                except ValueError:
                    msg = resp
            raise ClientException("Failed to delete role {} - {}".format(name, msg))

    def list(self, filter=None):
        """
        Returns the list of OSM role.

        :param filter:
        :returns:
        """
        filter_string = ''
        if filter:
            filter_string = '?{}'.format(filter)
        resp = self._http.get_cmd('{}{}'.format(self._apiBase, filter_string))
        # print('RESP: {}'.format(resp))
        if resp:
            return resp
        return list()

    def get(self, name):
        """
        Returns a specific OSM role based on name or id.

        :param name:
        :raises NotFound: when the role is not found.
        :returns: the specified role.
        """
        if utils.validate_uuid4(name):
            for role in self.list():
                if name == role['_id']:
                    return role
        else:
            for role in self.list():
                if name == role['name']:
                    return role
        raise NotFound("Role {} not found".format(name))
