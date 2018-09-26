#  Copyright (c) 2018 SONATA-NFV, 5GTANGO, Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, 5GTANGO, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
#
# This work has also been performed in the framework of the 5GTANGO project,
# funded by the European Commission under Grant number 761493 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.5gtango.eu).

import itertools as it
import yaml
import os
import logging

LOG = logging.getLogger(__name__)


def read_yaml(path):
    yml = None
    with open(path, "r") as f:
            try:
                yml = yaml.load(f)
            except yaml.YAMLError as ex:
                LOG.exception("YAML error while reading %r." % path)
                LOG.debug(ex)
    return yml


def write_yaml(path, data):
    with open(path, "w") as f:
        try:
            yaml.dump(data, f, default_flow_style=False)
        except yaml.YAMLError as ex:
            LOG.exception("YAML error while writing %r" % path)
            LOG.debug(ex)


def ensure_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)


def relative_path(path):
    if path.startswith("file://"):
        path = path.replace("file://", "", 1)
    if path.startswith("/"):
        path = path.replace("/", "", 1)
    return path


def compute_cartesian_product(p_dict):
    """
    Compute Cartesian product on parameter dict:
    In:
        {"number": [1,2,3], "color": ["orange","blue"] }
    Out:
        [ {"number": 1, "color": "orange"},
          {"number": 1, "color": "blue"},
          {"number": 2, "color": "orange"},
          {"number": 2, "color": "blue"},
          {"number": 3, "color": "orange"},
          {"number": 3, "color": "blue"}
        ]
    """
    p_names = sorted(p_dict)
    return [dict(
        zip(p_names, prod))
            for prod in it.product(
                    *(p_dict[n] for n in p_names))]
