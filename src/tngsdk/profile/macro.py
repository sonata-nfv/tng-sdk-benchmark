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
import coloredlogs
# import numpy as np
import re
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
        if is_macro(v):
            p = re.compile("\${.*}")
            match = p.search(v)
            if match:
                macro = match.group(0)
                list = macro_to_list(macro)
                new_list = []
                for value in list:
                    new_list.append(v.replace(macro, str(value)))
                d[k] = new_list
    return d


def is_macro(s):
    """
    Checks if string is a parameter macro.
    :param s: string
    :return: bool
    """
    if isinstance(s, str):
        if "${" in s:  # TODO improve: use regex
            return True
    return False


def macro_to_list(m):
    """
    Parses macro and translates it to a list.
    Loop macro: Unroll loop and create list.
    List macro: Translate macro list to Python list.
    :param m: macro as string
    :return: list
    """
    if "to" in m:
        # loop macro
        return loop_macro_to_list(m)
    else:
        # list macro
        return list_macro_to_list(m)


def loop_macro_to_list(m):
    """
    Unroll macro loop to list.
    :param m: macro string
    :return: list
    """
    r = list()
    m = m.strip("${}")
    m = re.split('to|step', m)
    # detect if the values should be float or int
    cls = float
    if not '.' in str(m):
        cls = int
    m = [cls(i) for i in m]
    step = DEFAULT_STEP
    if len(m) > 2:
        step = m[2]
    # unroll the given loop to a list of values
    for i in frange(m[0], m[1], step):
        r.append(i)
    return r


def list_macro_to_list(m):
    """
    Translate macro list to Python list.
    :param m: macro sting
    :return: list
    """
    m = m.strip("${}")
    m = re.split(',', m)
    # detect if the values should be float or int
    cls = str
    if is_number(str(m)):  
        cls = float
        if not '.' in str(m):
            cls = int
    m = [cls(i) for i in m]
    return m


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
        if x >= stop:
            return
        yield x
        x += step

def is_number(s):
    try:
        float(s) 
    except ValueError:
        return False
    return True

