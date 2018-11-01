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
import os
import docker


LOG = logging.getLogger(os.path.basename(__file__))


class EmuDockerClient(object):
    """
    Wraps docker client to remotly control vim-emu containers.
    Doc: https://docker-py.readthedocs.io/en/stable/
    """

    def __init__(self, endpoint):
        self.endpoint = "{}".format(endpoint)
        self.client = None
        try:
            self.client = docker.DockerClient(
                base_url=self.endpoint, timeout=5)
            self.client.containers.list()  # check connection
            LOG.debug("Initialized EmuDocker client for {}".format(endpoint))
        except BaseException as ex:
            LOG.exception(ex)
            LOG.error("Couldn't conncet to Docker service on target machine.")
            LOG.error("Stopping.")
            exit(1)

    def execute(self, container_name, cmd, logfile):
        """
        Run command on container.
        Non blocking.
        """
        assert(container_name is not None)
        if cmd is None:
            return None  # skip command execution
        container_name = "mn.{}".format(container_name)
        LOG.debug("Execute on '{}' to logfile '{}': '{}'".format(
            container_name, logfile, cmd))
        # get the container
        c = self.client.containers.get(container_name)
        assert(c is not None)
        # build full cmd
        cmd = "bash -c 'nohup {} > {} 2>&1 &'".format(cmd, logfile)
        # execute command in target container (blocks if detach=False)
        rcode, rdata = c.exec_run(cmd, stdin=False, stdout=False, detach=False)
        LOG.debug("Out (empty in detach mode): return code: {}; stdout: '{}'"
                  .format(rcode, rdata))
        LOG.debug("Top on '{}': {}".format(container_name, c.top()))
