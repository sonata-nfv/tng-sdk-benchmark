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


import paramiko
import json
import logging
import requests
import time
import threading
import yaml
import os
import stat
import argparse

# define some constants for easy changing
# will likely be removed as default values dont make sense past testing
PATH_COMMAND = "cd ~/son-emu"
EXEC_COMMAND = "sudo python src/emuvim/examples/profiling.py"
REMOTE_LOGGING_DEFAULT = False

# create a Logger
logging.basicConfig()
LOG = logging.getLogger("SON-Profile Emulator")
LOG.setLevel(logging.DEBUG)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
paramiko_logger = logging.getLogger("paramiko")
paramiko_logger.setLevel(logging.WARNING)

"""
 A class which provides methods to do experiments with service packages
"""
class Emulator:

    """
     Initialize with a list of descriptors of workers to run experiments on
     :tpd: target platforms descriptor. A dictionary describing the remote hosts on which service can be tested or a dictionary containing a key which value is the descriptor
     :remote_logging: Set it to True if logs of the remote topology should be shown in the local log files.
        WARNING: They will be shown at the end of each experiment, will not neccessarily be complete and are output as logging error, probably because of mininet
    """
    def __init__(self, tpd, remote_logging=REMOTE_LOGGING_DEFAULT):
        # if the whole config dictionary has been given, extract only the target platforms
        # a descriptor version should only be in the top level of the file
        if "descriptor_version" in tpd:
            tpd = tpd.get("target_platforms")
            LOG.debug("Found target platforms in dictionary.")

        # save the emulator nodes
        self.emulator_nodes = {tpd[i].get('name'):tpd[i] for i in range(len(tpd))}

        # check for empty emulator node lists
        if not len(self.emulator_nodes):
            LOG.error("No remote hosts specified.")
            raise Exception("Need at least one emulator to be specified in the target platforms descriptor.")

        # all nodes are available at the start
        self.available_nodes = list(self.emulator_nodes.keys())
        LOG.info("%r nodes found."%len(self.emulator_nodes))
        LOG.debug("List of emulator nodes: %r"%self.emulator_nodes.keys())

        # save the remote_logging flag
        if remote_logging:
            LOG.info("Remote logs will be shown.")
        else:
            LOG.info("Remote logs will not be shown.")
        self.remote_logging = remote_logging

    """
     Conduct multiple experiments using the do_experiment method
     All experiments are started in a separate thread
     The order in which the experiments are run is not fixed!
     :experiments: a dictionary mapping from run_id to a dictionary containing information about the experiment
    """
    def do_experiment_series(self, experiments):
        # start the experiments in separate threads
        LOG.info("%r experiments will be run."%len(experiments.keys()))

        for i in experiments.keys():
            # choose which node to run the experiment on
            # the first idle node would be best
            while not self.available_nodes:
                time.sleep(1)
            node_name = self.available_nodes.pop()

            t = threading.Thread(target=self._do_experiment_wrapper, kwargs={"run_id":i, "exp_dict":experiments[i], "node_name":node_name})
            t.start()

    """
        A wrapper method needed to make worker nodes available after execution
        :experiment: the experiment to be run
        :run_id: the id of the experiment to be run
        :exp_dict: the dictionary describing the experiment
        :node_name: the name of the node on which the experiment is run
    """
    def _do_experiment_wrapper(self, run_id, exp_dict, node_name):
        # check whether the specified worker exists
        if not node_name in self.emulator_nodes:
            LOG.critical("Run %r: Specified node does not exist."%run_id)
            raise Exception("The specified node does not exist.")
        node=self.emulator_nodes[node_name]

        experiment = Experiment(exp_dict=exp_dict, run_id=run_id, node=node, remote_logging=self.remote_logging)

        t = threading.Thread(target=experiment.exec_experiment)
        t.start()
        t.join()
        self.available_nodes.append(node_name)

class Experiment:
    """

    """
    def __init__(self, exp_dict, run_id, node, remote_logging=REMOTE_LOGGING_DEFAULT, max_retries=3):
        # save the given information
        self.exp_dict = exp_dict
        self.run_id = run_id
        self.node = node
        self.remote_logging = remote_logging
        self.retries_left = max_retries

        self.path_to_pkg = os.path.expanduser(exp_dict.get('sonfile'))
        self._log_debug("Path to package: %r."%self.path_to_pkg)

        # save the time limit. Will be overwritten later if experiment series is run.
        # if it is run as standalone, will not be overwritten
        self.time_limit = exp_dict.get('time_limit')

        self.address = node["address"]
        self._log_debug("Remote address is %r."%self.address)

        self.package_port = node.get('package_port', 5000)
        self._log_debug("Port for packages is %r."%self.package_port)

        self.ssh_port = node.get('ssh_port', 22)
        self._log_debug("SSH port is %r."%self.ssh_port)

        self.username = node.get('ssh_user')
        self._log_debug("Username for ssh connection is %r."%self.username)

        self.key_loc = os.path.expanduser(node.get('ssh_key_loc'))
        self._log_debug("Location of ssh key is %r."%self.key_loc)

        # import the RSA key
        self.pkey = paramiko.RSAKey.from_private_key_file(self.key_loc)

        # a ped file is only given if an experiment series is run
        self.mp_start_command = dict()
        self.mp_commands = dict()
        self.mp_stop_command = dict()

        if "experiment_configuration" in self.exp_dict:
            self._log_info("PED data found. Updating data.")
            self._update_with_ped_data()
        else:
            self._log_info("No PED data found. Running in single experiment mode.")

        self.payload_done = False


    """
     If an experiment series is run, a ped is given containing all necessary information
     If it is a single experiment, there is no ped
     Expected ped structure:
       service_experiments OR function_experiments:
       - name: "..." (not used)
         measurement_points:
         - name: "..."
           cmd_start: "..." (optional)
           commands: "..."  (optional)
           cmd_stop: "..."  (optional)
    """
    def _update_with_ped_data(self):
        # get the experiment summary from the ped
        exp_conf = self.exp_dict.get('experiment_configuration')
        exp_data = exp_conf.get('experiment')
        exp_params = exp_conf.get('parameter')
        # set the time limit
        self.time_limit = int(exp_data.get('time_limit'))
        self._log_debug("Time limit set to %r."%self.time_limit)

        # get a list of all the measurement points and extract the commands to be run in them
        mp_names = [exp_data.get("measurement_points")[i].get('name') for i in range(len(exp_data.get("measurement_points")))]
        for n in mp_names:
            cmd_start = exp_params.get("measurement_point:%s:cmd_start"%n)
            self.mp_start_command[n] = cmd_start
            self.mp_commands[n] = exp_params.get("measurement_point:%s:commands"%n) or dict()
            cmd_stop = exp_params.get("measurement_point:%s:cmd_stop"%n)
            self.mp_stop_command[n] = cmd_stop


    """
     Conduct a single experiment with given values
     One experiment consists of:
     1) starting the topology remotely on a server
     2) uploading the service package
     3) starting the service
     4) wait a specified amount of time
     5) stop the service
     6) gather results
     7) clean up results from remote server
     8) close the connection
     :node: the emulator node to be used for the experiment
    """
    def exec_experiment(self):
        # connect to the client per ssh
        ssh = paramiko.client.SSHClient()

        # set policy for unknown hosts or import the keys
        # for now, we just add all new keys instead of adding certain ones
        ssh.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())

        # connect to the remote host via ssh
        ssh.connect(self.address, port=self.ssh_port, username=self.username, pkey=self.pkey)
        self._log_info("Connected to remote host.")

        # start the profiling topology on the client
        # use a seperate thread to prevent blocking by the topology
        self._log_info("Starting remote topology.")
        self._exec_command("%s;%s -p %s"%(PATH_COMMAND,EXEC_COMMAND, self.package_port))

        # wait a short while to let the topology start
        time.sleep(5)

        try:
            service_uuid = self._run_experiment_payload(ssh=ssh)
        finally:
            # stop the remote topology
            self._log_info("Stopping remote topology.")
            self._exec_command('sudo pkill -f "%s -p %s"'%(EXEC_COMMAND, self.package_port))

            if self.payload_done:
                # gather the results etc.
                sftp = ssh.open_sftp()
                # switch to directory containing relevant files
                sftp.chdir("/tmp/results/%s/"%service_uuid)

                self._copy_files_from_remote(sftp=sftp)

                # remove all temporary files and directories from the remote host
                self._log_info("Removing results on remote host.")
                self._exec_command("sudo rm -r /tmp/results/%s"%service_uuid)

                self._log_info("Closing connections.")
                # close the sftp connection
                sftp.close()

            # close the ssh connection
            ssh.close()

            # if experiment failed, repeat. TODO: Find a way to do this without recursion
            if not self.payload_done and self.retries_left>0:
                self.retries_left-=1
                self.exec_experiment()

    def _log_debug(self, log_message):
        LOG.debug("Run %r: %s"%(self.run_id, log_message))

    def _log_info(self, log_message):
        LOG.info("Run %r: %s"%(self.run_id, log_message))

    def _log_error(self, log_message):
        LOG.error("Run %r: %s"%(self.run_id, log_message))

    """
        Upload and execute the specified package for a set amount of time, returns the service uuid
    """
    def _run_experiment_payload(self, ssh=None):
        remote_url = "http://%s:%s"%(self.address, self.package_port)
        # upload the service package
        self._log_info("Path to package is %r"%self.path_to_pkg)
        f = open(self.path_to_pkg, "rb")
        self._log_info("Uploading package to %r."%remote_url)
        r1 = requests.post("%s/packages"%(remote_url), files={"package":f})
        service_uuid = json.loads(r1.text).get("service_uuid")
        self._log_debug("Service uuid is %s."%service_uuid)

        # start the service
        r2 = requests.post("%s/instantiations"%(remote_url), data=json.dumps({"service_uuid":service_uuid}))
        service_instance_uuid = json.loads(r2.text).get("service_instance_uuid")
        self._log_debug("Service instance uuid is %s."%service_instance_uuid)

        # run commands if experiment series
        measurement_points = self.mp_commands.keys()
        if measurement_points:
            if not ssh:
                raise Exception('A valid ssh connection is needed to execute commands in measurement points.')
            for mp in measurement_points:
                docker_name = 'mn.%s'%mp

                time.sleep(3)

                commands_thread = threading.Thread(target=self._run_commands, kwargs={"mp":mp, "docker_name":docker_name})
                self.comm_thread_stay_alive = True
                commands_thread.start()

        # let the service run for a specified time
        self._log_info("Sleep for %r seconds."%self.time_limit)
        time.sleep(self.time_limit)

        # execute stop commands in measurement points
        if measurement_points:
            if not ssh:
                raise Exception('A valid ssh connection is needed to execute commands in measurement points.')
            for mp in measurement_points:
                docker_name = "mn.%s"%mp
                # stop the thread executing commands if it is not yet done
                self.comm_thread_stay_alive = False
                stop_cmd = self.mp_stop_command.get(mp)
                if stop_cmd:
                    self._log_debug("Executing stop script %r in docker container %r on %r."%(stop_cmd, docker_name, self.node.get('name')))
                    t=self._exec_command(command='sudo docker exec --privileged %s sh -c %r'%(docker_name, stop_cmd))
                    t.join()

        # stop the service
        self._log_info("Stopping service")
        requests.delete("%s/instantiations"%(remote_url), data=json.dumps({"service_uuid":service_uuid, "service_instance_uuid":service_instance_uuid}))

        # sometimes, the package upload fails, so we validate the execution of the payload
        self.payload_done = True

        return service_uuid

    """

    """
    def _run_commands(self, mp, docker_name):
        commands = self.mp_commands.get(mp)
        commands[00] = self.mp_start_command.get(mp)
        comm_keys = commands.keys()
        for i in range(100):
            if not self.comm_thread_stay_alive:
                break
            if i in comm_keys:
                c = commands.get(i)
                self._log_debug("Executing %r in docker container %r on %r."%(c, docker_name, self.node.get("name")))
                cmd_string = 'sudo docker exec --privileged %s sh -c %r'%(docker_name, c)
                t=self._exec_command(cmd_string)
                t.join()
        self.comm_thread_stay_alive = False




    """
        Copy the results of the experiment to a local folder
        :sftp: the sftp client used to copy the files
        :run_id: the id of the experiment run
    """
    def _copy_files_from_remote(self, sftp):
        # the path to which the files will be copied
        local_path = "result/%r"%self.run_id

        # all files in the folder have to be copied, directories have to be handled differently
        files_to_copy = sftp.listdir()
        # as long as there are files to copy
        self._log_info("Copying results from remote hosts.")
        while files_to_copy:
            # get next "file"
            file_path = files_to_copy.pop()
            # if the "file" is a directory, put all files contained in the directory in the list of files to be copied
            file_mode = sftp.stat(file_path).st_mode
            if stat.S_ISDIR(file_mode):
                self._log_debug("Found directory %s"%file_path)
                more_files = sftp.listdir(path=file_path)
                for f in more_files:
                    # we need the full path
                    files_to_copy.append(os.path.join(file_path,f))
                if not os.path.exists(os.path.join(local_path, file_path)):
                    os.makedirs(os.path.join(local_path, file_path))
            elif stat.S_ISREG(file_mode):
                # the "file" is an actual file
                self._log_debug("Found file %s"%file_path)
                # copy the file to the local system, preserving the folder hierarchy
                sftp.get(file_path, os.path.join(local_path,file_path))
            else:
                # neither file nor directory
                # skip it
                self._log_debug("Skipping %s: Neither file nor directory"%file_path)


    def _exec_command(self, command):
        t = threading.Thread(target=self._exec_command_thread, kwargs={"command":command})
        t.start()
        return t

    """
    Helper method to be called in a thread
    A single command is executed on a remote server via ssh
    """
    def _exec_command_thread(self, command):
        # connect to the client per ssh
        ssh = paramiko.client.SSHClient()

        # set policy for unknown hosts or import the keys
        # for now, we just add all new keys instead of adding certain ones
        ssh.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())

        # connect to the remote host via ssh
        ssh.connect(self.address, port=self.ssh_port, username=self.username, pkey=self.pkey)
        comm_in, comm_out, comm_err = ssh.exec_command(command)
        comm_in.close()
        while not (comm_out.channel.exit_status_ready() and comm_err.channel.exit_status_ready()):
            for line in comm_out.read().splitlines():
                if self.remote_logging:
                    self._log_debug(line)
            for line in comm_err.read().splitlines():
                if self.remote_logging:
                    self._log_error(line)

        ssh.close()

"""
 Checks whether the given file path is an existing config file
"""
def config_file_exists(file_path):
    if not os.path.exists(file_path):
        raise argparse.ArgumentError("%r needs to be an existing file."%file_path)
    with open(file_path, "r") as f:
        config_dict = yaml.load(f)
        if not "target_platforms" in config_dict:
            raise argparse.ArgumentTypeError("%r does not contain a target platforms descriptor."%file_path)
    f.close()
    return file_path

"""
 Checks whether the given file_path if an existing file
"""
def package_file_exists(file_path):
    if not os.path.exists(file_path):
        raise argparse.ArgumentTypeError("%r needs to be an existing file."%file_path)
    return file_path

if __name__=='__main__':
    parser = argparse.ArgumentParser(description="Run experiments with the given son packages")
    parser.add_argument("--time", "-t",
            help="The runtime of every experiment",
            type=int, default=10, required=False, dest="time", metavar="seconds")
    parser.add_argument("--remote-logging",
            help="Enable showing logs of remote topology",
            action="store_true", required=False, dest="rem_log")
    parser.add_argument("--config-file", "-c",
            help="Specify which config file to use for specification of remote hosts",
            required=False, dest="config", type=config_file_exists, metavar="Config Path")
    parser.add_argument("package_path",
            help="Path to a package",
            nargs="+", type=package_file_exists, metavar="Package Path")
    args = parser.parse_args()

    config_path = args.config
    if not config_path:
        config_path = "src/son/profile/config.yml"
    with open(config_path, "r") as tpd:
        conf = yaml.load(tpd)
    tpd.close()
    remote_logging = args.rem_log
    e = Emulator(tpd=conf, remote_logging=remote_logging)
    experiments = {i: {'sonfile':args.package_path[i], 'time_limit':args.time} for i in range(len(args.package_path))}
    e.do_experiment_series(experiments)
