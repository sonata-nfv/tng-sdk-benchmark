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

import time
from uuid import UUID
import hashlib
import tarfile
import re
import yaml


def wait_for_value(func, result=True, wait_time=10, catch_exception=None):
    maxtime = time.time() + wait_time
    while time.time() < maxtime:
        try:
            if func() == result:
                return True
        except catch_exception:
            pass
        time.sleep(5)
    try:
        return func() == result
    except catch_exception:
        return False


def validate_uuid4(uuid_text):
    try:
        UUID(uuid_text)
        return True
    except (ValueError, TypeError):
        return False


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_key_val_from_pkg(descriptor_file):
    # method opens up a package and finds the name of the resulting
    # descriptor (vnfd or nsd name)
    tar = tarfile.open(descriptor_file)
    yamlfile = None
    for member in tar.getmembers():
        if (re.match('.*.yaml', member.name) and
                len(member.name.split('/')) == 2):
            yamlfile = member.name
            break
    if yamlfile is None:
        return None

    dict = yaml.load(tar.extractfile(yamlfile))
    result = {}
    for k1, v1 in list(dict.items()):
        if not k1.endswith('-catalog'):
            continue
        for k2, v2 in list(v1.items()):
            if not k2.endswith('nsd') and not k2.endswith('vnfd'):
                continue

            if 'nsd' in k2:
                result['type'] = 'nsd'
            else:
                result['type'] = 'vnfd'

            for entry in v2:
                for k3, v3 in list(entry.items()):
                    # strip off preceeding chars before :
                    key_name = k3.split(':').pop()

                    result[key_name] = v3
    tar.close()
    return result
