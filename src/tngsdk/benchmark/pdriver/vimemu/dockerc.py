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
import os
import docker
import tarfile
import threading
import time
import json
from tngsdk.benchmark.logger import TangoLogger
from tngsdk.benchmark.helper import ensure_dir

LOG = TangoLogger.getLogger(__name__)


MONITORING_RATE = .5  # monitoring records per second
PATH_TEMP_TAR = "/tmp/tng-bench/.tngbench_share.tar"


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
            self.apiclient = docker.APIClient(
                base_url=self.endpoint, timeout=5)
            self.client.containers.list()  # check connection
            LOG.debug("Initialized EmuDocker client for {}".format(endpoint))
        except BaseException as ex:
            LOG.exception(ex)
            LOG.error("Couldn't conncet to Docker service on target machine.")
            LOG.error("Stopping.")
            exit(1)

    def execute(self, container_name, cmd, logfile, block=False):
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
        postfix = ""
        if not block:
            postfix = " &"
        cmd = "bash -c 'nohup {} > {} 2>&1{}'".format(cmd, logfile, postfix)
        # execute command in target container (blocks if detach=False)
        rcode, rdata = c.exec_run(
            cmd, stdin=False, stdout=False, detach=(not block))
        LOG.debug("Out (empty in detach mode): return code: {}; stdout: '{}'"
                  .format(rcode, rdata))
        LOG.debug("Top on '{}': {}".format(container_name, c.top()))

    def list_emu_containers(self):
        """
        Return all containers with "mn." as name prefix.
        """
        return [c for c in self.client.containers.list() if "mn." in c.name]

    def copy_folder(self, container_name, src_path, dst_path):
        """
        Copy all files from given folder (src_path) to
        local folder (dst_path).
        """
        LOG.debug("Collect files from docker {}: {} -> {}".format(
            container_name, src_path, dst_path))
        try:
            c = self.client.containers.get(container_name)
            strm, _ = c.get_archive(src_path)
            # write to intermediate tar
            ensure_dir(PATH_TEMP_TAR)
            with open(PATH_TEMP_TAR, 'wb') as f:
                for d in strm:
                    f.write(d)
            tar = tarfile.TarFile(PATH_TEMP_TAR)
            tar.extractall(dst_path)
            os.remove(PATH_TEMP_TAR)
        except BaseException as ex:
            LOG.warning("Could not collect froles from docker {}: {}"
                        .format(container_name, ex))

    def store_logs(self, container_name, dst_path):
        """
        Get logs from given container and store them to dst_path.
        """
        LOG.debug("Collect logs from docker {} -> {}".format(
            container_name, dst_path))
        c = self.client.containers.get(container_name)
        try:
            with open(dst_path, "w") as f:
                # can be emtpy since we do not use Docker's default CMD ep.
                f.write(str(c.logs()))
        except IOError as ex:
            LOG.warning("Could not store logs to {}: {}".format(dst_path, ex))

    def get_stats(self):
        """
        Fetches Docker stats for all containers in the system.
        Returns dict: c.name -> stats_dict from Docker API
        """
        all_stats = dict()
        for c in self.list_emu_containers():
            s = self.apiclient.stats(c.name, stream=False, decode=False)
            s["name"] = c.name
            # LOG.debug("Received Docker stats for {}: {}".format(c.name, s))
            all_stats[c.name] = s
        return all_stats


class EmuDockerMonitor(threading.Thread):
    """
    Thread that periodically polls Docker statistics and
    puts them into the list: self.recorded_stats to be used
    later.
    """

    def __init__(self, client, wait_time):
        self.client = client
        self.wait_time = wait_time
        self.recorded_stats = None
        super().__init__()

    def run(self):
        # FIXME each call needs time, so data of containers is NOT aligned
        # FIXME docker stats seems to be not very performat -> use low rates
        time_start = time.time()
        self.recorded_stats = list()
        while(time.time() - time_start < self.wait_time):
            # get docker stats and store as tuple (time, stats_dict_dict)
            self.recorded_stats.append((time.time(),
                                        self.client.get_stats()))
            # wait
            time.sleep(1.0/MONITORING_RATE)
        LOG.debug("Recorded {} Docker stats records"
                  .format(len(self.recorded_stats)))

    def store_stats(self, dst_path):
        LOG.debug("Writing Docker stats: {}".format(dst_path))
        with open(dst_path, "w") as f:
            f.write(json.dumps(self.recorded_stats))
