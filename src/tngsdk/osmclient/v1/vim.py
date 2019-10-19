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
OSM vim API handling
"""

from osmclient.common.exceptions import ClientException
from osmclient.common.exceptions import NotFound
import yaml 
import time


class Vim(object):
    def __init__(self, http=None, ro_http=None, client=None):
        self._client = client
        self._ro_http = ro_http
        self._http = http

    def _attach(self, vim_name, vim_account):
        tenant_name = 'osm'
        tenant = self._get_ro_tenant()
        if tenant is None:
            raise ClientException("tenant {} not found".format(tenant_name))

        datacenter = self._get_ro_datacenter(vim_name)
        if datacenter is None:
            raise Exception('datacenter {} not found'.format(vim_name))

        return self._ro_http.post_cmd('openmano/{}/datacenters/{}'
                                      .format(tenant['uuid'],
                                              datacenter['uuid']), vim_account)

    def _detach(self, vim_name):
        tenant_name = 'osm'
        tenant = self._get_ro_tenant()
        if tenant is None:
            raise ClientException("tenant {} not found".format(tenant_name))
        return self._ro_http.delete_cmd('openmano/{}/datacenters/{}'
                                        .format(tenant["uuid"], vim_name))

    def create(self, name, vim_access):
        vim_account = {}
        vim_account['datacenter'] = {}

        # currently assumes vim_acc
        if ('vim-type' not in vim_access): 
           #'openstack' not in vim_access['vim-type']):
            raise Exception("vim type not provided")

        vim_account['datacenter']['name'] = name
        vim_account['datacenter']['type'] = vim_access['vim-type']

        vim_config = {}
        if 'config' in vim_access and vim_access['config'] is not None:
           vim_config = yaml.load(vim_access['config'])

        if vim_config:
            vim_account['datacenter']['config'] = vim_config

        vim_account = self.update_vim_account_dict(vim_account, vim_access, vim_config)

        resp = self._ro_http.post_cmd('openmano/datacenters', vim_account)
        if resp and 'error' in resp:
            raise ClientException("failed to create vim")
        else:
            self._attach(name, vim_account)
            self._update_ro_accounts()


    def _update_ro_accounts(self):
        get_ro_accounts = self._http.get_cmd('api/operational/{}ro-account'
                    .format(self._client.so_rbac_project_path))
        if not get_ro_accounts or 'rw-ro-account:ro-account' not in get_ro_accounts:
            return
        for account in get_ro_accounts['rw-ro-account:ro-account']['account']:
            if account['ro-account-type'] == 'openmano':
                # Refresh the Account Status
                refresh_body = {"input": {
                                            "ro-account": account['name'], 
                                            "project-name": self._client._so_project
                                        }
                                }
                refresh_status = self._http.post_cmd('api/operations/update-ro-account-status',
                    refresh_body)
                if refresh_status and 'error' in refresh_status:
                    raise ClientException("Failed to refersh RO Account Status")
    

    def update_vim_account_dict(self, vim_account, vim_access, vim_config):
        if vim_access['vim-type'] == 'vmware':
            if 'admin_username' in vim_config:
                vim_account['datacenter']['admin_username'] = vim_config['admin_username']
            if 'admin_password' in vim_config:
                vim_account['datacenter']['admin_password'] = vim_config['admin_password']
            if 'nsx_manager' in vim_config:
                vim_account['datacenter']['nsx_manager'] = vim_config['nsx_manager']
            if 'nsx_user' in vim_config:
                vim_account['datacenter']['nsx_user'] = vim_config['nsx_user']
            if 'nsx_password' in vim_config:
                vim_account['datacenter']['nsx_password'] = vim_config['nsx_password']
            if 'orgname' in vim_config:
                vim_account['datacenter']['orgname'] = vim_config['orgname']
            if 'vcenter_ip' in vim_config:
                vim_account['datacenter']['vcenter_ip'] = vim_config['vcenter_ip']
            if 'vcenter_user' in vim_config:
                vim_account['datacenter']['vcenter_user'] = vim_config['vcenter_user']
            if 'vcenter_password' in vim_config:
                vim_account['datacenter']['vcenter_password'] = vim_config['vcenter_password']
            if 'vcenter_port' in vim_config:
                vim_account['datacenter']['vcenter_port'] = vim_config['vcenter_port']
            vim_account['datacenter']['vim_url'] = vim_access['vim-url']
            vim_account['datacenter']['vim_url_admin'] = vim_access['vim-url']
            vim_account['datacenter']['description'] = vim_access['description']
            vim_account['datacenter']['vim_username'] = vim_access['vim-username']
            vim_account['datacenter']['vim_password'] = vim_access['vim-password']
            vim_account['datacenter']['vim_tenant_name'] = vim_access['vim-tenant-name']
        else:
            vim_account['datacenter']['vim_url'] = vim_access['vim-url']
            vim_account['datacenter']['vim_url_admin'] = vim_access['vim-url']
            vim_account['datacenter']['description'] = vim_access['description']
            vim_account['datacenter']['vim_username'] = vim_access['vim-username']
            vim_account['datacenter']['vim_password'] = vim_access['vim-password']
            vim_account['datacenter']['vim_tenant_name'] = vim_access['vim-tenant-name']
        return vim_account

    def delete(self, vim_name):
        # first detach
        self._detach(vim_name)
        # detach.  continue if error,
        # it could be the datacenter is left without attachment
        resp = self._ro_http.delete_cmd('openmano/datacenters/{}'
                                                    .format(vim_name))
        if 'result' not in resp:
            raise ClientException("failed to delete vim {} - {}".format(vim_name, resp))
        self._update_ro_accounts()

    def list(self, ro_update):
        if ro_update:
            self._update_ro_accounts()
            # the ro_update needs to be made synchronous, for now this works around the issue
            # and waits a resonable amount of time for the update to finish
            time.sleep(2)

        if self._client._so_version == 'v3':
            resp = self._http.get_cmd('v1/api/operational/{}ro-account-state'
                    .format(self._client.so_rbac_project_path))
            datacenters = []
            if not resp or 'rw-ro-account:ro-account-state' not in resp:
                return list()

            ro_accounts = resp['rw-ro-account:ro-account-state']
            for ro_account in ro_accounts['account']:
                if 'datacenters' not in ro_account:
                    continue
                if 'datacenters' not in ro_account['datacenters']:
                    continue
                for datacenter in ro_account['datacenters']['datacenters']:
                    datacenters.append({"name": datacenter['name'], "uuid": datacenter['uuid']
                        if 'uuid' in datacenter else None}) 

            vim_accounts = datacenters
            return vim_accounts
        else:
            # Backwards Compatibility
            resp = self._http.get_cmd('v1/api/operational/datacenters')
            if not resp or 'rw-launchpad:datacenters' not in resp:
                return list()
 
            datacenters = resp['rw-launchpad:datacenters']
 
            vim_accounts = list()
            if 'ro-accounts' not in datacenters:
                return vim_accounts
 
            tenant = self._get_ro_tenant()
            if tenant is None:
                return vim_accounts
 
            for roaccount in datacenters['ro-accounts']:
                if 'datacenters' not in roaccount:
                    continue
                for datacenter in roaccount['datacenters']:
                    vim_accounts.append(self._get_ro_datacenter(datacenter['name'],
                                                              tenant['uuid']))
            return vim_accounts

    def _get_ro_tenant(self, name='osm'):
        resp = self._ro_http.get_cmd('openmano/tenants/{}'.format(name))

        if not resp:
            return None

        if 'tenant' in resp and 'uuid' in resp['tenant']:
            return resp['tenant']
        else:
            return None

    def _get_ro_datacenter(self, name, tenant_uuid='any'):
        resp = self._ro_http.get_cmd('openmano/{}/datacenters/{}'
                                     .format(tenant_uuid, name))
        if not resp:
            raise NotFound("datacenter {} not found".format(name))

        if 'datacenter' in resp and 'uuid' in resp['datacenter']:
            return resp['datacenter']
        else:
            raise NotFound("datacenter {} not found".format(name))

    def get(self, name):
        tenant = self._get_ro_tenant()
        if tenant is None:
            raise NotFound("no ro tenant found")

        return self._get_ro_datacenter(name, tenant['uuid'])

    def get_datacenter(self, name):
        if self._client._so_version == 'v3':
            resp = self._http.get_cmd('v1/api/operational/{}ro-account-state'
                    .format(self._client.so_rbac_project_path))
            if not resp:
                return None, None

            if not resp or 'rw-ro-account:ro-account-state' not in resp:
                return None, None

            ro_accounts = resp['rw-ro-account:ro-account-state']
            for ro_account in ro_accounts['account']:
                if 'datacenters' not in ro_account:
                    continue
                if 'datacenters' not in ro_account['datacenters']:
                    continue
                for datacenter in ro_account['datacenters']['datacenters']:
                    if datacenter['name'] == name:
                        return datacenter, ro_account['name']        
            return None, None
        else:
            # Backwards Compatibility
            resp = self._http.get_cmd('v1/api/operational/datacenters')
            if not resp:
                return None
 
            if not resp or 'rw-launchpad:datacenters' not in resp:
                return None
            if 'ro-accounts' not in resp['rw-launchpad:datacenters']:
                return None
            for roaccount in resp['rw-launchpad:datacenters']['ro-accounts']:
                if 'datacenters' not in roaccount:
                    continue
                for datacenter in roaccount['datacenters']:
                    if datacenter['name'] == name:
                        return datacenter
            return None

    def get_resource_orchestrator(self):
        resp = self._http.get_cmd('v1/api/operational/{}resource-orchestrator'
                .format(self._client.so_rbac_project_path))

        if not resp or 'rw-launchpad:resource-orchestrator' not in resp:
            return None
        return resp['rw-launchpad:resource-orchestrator']
