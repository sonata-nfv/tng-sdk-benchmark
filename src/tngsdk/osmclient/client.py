# Copyright 2017-2018 Sandvine
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
OSM client entry point
"""

from tngsdk.osmclient.v1 import client as client
from tngsdk.osmclient.sol005 import client as sol005client


def Client(version=1, host=None, sol005=False, *args, **kwargs):
    if not sol005:
        if version == 1:
            return client.Client(host, *args, **kwargs)
        else:
            raise Exception("Unsupported client version")
    else:
        if version == 1:
            return sol005client.Client(host, *args, **kwargs)
        else:
            raise Exception("Unsupported client version")
