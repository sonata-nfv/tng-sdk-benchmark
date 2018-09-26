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

import logging


LOG = logging.getLogger(__name__)


# default step size for loop macro
DEFAULT_STEP = 1.0


def rewrite_parameter_macros_to_lists(d):
    """
    Search for macros in dictionary values and expand the to lists.
    :param d: input dict
    :return: result dict
    """
    for k, v in d.items():
        d[k] = expand_parameters(v)
    return d


def expand_parameters(p):
    """
    Expand single values, lists or dicts to a
    list of parameters.
    """
    if p is None:
        return [None]
    if isinstance(p, int) or isinstance(p, float):
        return [p]
    elif isinstance(p, list):
        return p
    elif isinstance(p, dict):
        try:
            assert("min" in p)
            assert("max" in p)
            # assert("step" in p)
            return list(
                frange(p.get("min"),
                       p.get("max"),
                       p.get("step", DEFAULT_STEP)))
        except BaseException as ex:
            LOG.exception("AssertionError in dict expansion: {}"
                          .format(ex))
    # default: no expansion (e.g. for strings)
    return p


def frange(start, stop, step):
    """
    Floating point range generator.
    Own implementation to avoid numpy dependency.
    :param start: float
    :param stop: float
    :param step: float
    :return: None
    """
    # TODO ugly. Replace by numpy.arange or linspace.
    x = start
    while True:
        if round(x, 4) > stop:
            return
        yield round(x, 4)  # attention: we do some rounding here
        x += step
