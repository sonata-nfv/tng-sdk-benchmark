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

#
# Attention: This module requires Python2.7 because of its dependencies
# to vim-emu.
#
import logging
import sys
import argparse
import coloredlogs
import multiprocessing as mp
import time
import signal
import datetime
import platform
from ctypes import c_bool
from flask import Flask, Blueprint
from flask_restplus import Resource, Api, Namespace
from werkzeug.contrib.fixers import ProxyFix
from gevent.pywsgi import WSGIServer
# Hotfix:
if "2.7" in str(platform.python_version()):
    # pylint: disable=E0402
    from emuvim.dcemulator.net import DCNetwork
    from mininet.log import setLogLevel
    from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint
    from emuvim.api.tango import TangoLLCMEndpoint


LOG = logging.getLogger(__name__)


def parse_args(input_args=None):
    parser = argparse.ArgumentParser(
        description="5GTANGO tng-bench-emusrv")

    parser.add_argument(
        "-v",
        "--verbose",
        help="Output debug messages.",
        required=False,
        default=False,
        dest="verbose",
        action="store_true")

    parser.add_argument(
        "--learning",
        help="Enable learning switch for E-LANs.",
        required=False,
        default=False,
        dest="learning",
        action="store_true")

    parser.add_argument(
        "--address",
        help="Listen address of REST API."
        + "\nDefault: 0.0.0.0",
        required=False,
        default="0.0.0.0",
        dest="service_address")

    parser.add_argument(
        "--port",
        help="TCP port of REST API."
        + "\nDefault: 4999",
        required=False,
        default=4999,
        dest="service_port")
    if input_args is None:
        input_args = sys.argv[1:]
    return parser.parse_args(input_args)


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
blueprint = Blueprint('api', __name__, url_prefix="/api")
api_v1 = Namespace("v1", description="tng-bench-emusrv API v1")
api = Api(blueprint,
          version="0.1",
          title='5GTANGO tng-bench-emusrv API',
          description="5GTANGO tng-package REST API ")
app.register_blueprint(blueprint)
app.emulation_process = None
app.emulation_process_queue = None
api.add_namespace(api_v1)
http_server = None


def serve_forever(args, debug=True):
    """
    Start REST API server. Blocks.
    """
    global http_server
    app.cliargs = args
    # app.run(host=args.service_address,
    #       port=args.service_port,
    #       debug=debug)
    http_server = WSGIServer(
        (args.service_address, args.service_port), app)
    http_server.serve_forever()


def stop_serve(signum, frame):
    """
    Stop REST API and emulation.
    """
    stop_emulation()
    http_server.close()


def main():
    """
    Entrypoint: tng-bench-emusrv
    """
    args = parse_args()
    if args.verbose:
        coloredlogs.install(level="DEBUG")
    else:
        coloredlogs.install(level="INFO")
    LOG.info("Starting tng-bench-emusrv server ... CTRL+C to exit.")
    signal.signal(signal.SIGINT, stop_serve)
    signal.signal(signal.SIGTERM, stop_serve)
    serve_forever(args)


@api_v1.route("/emulation")
class EmulationEndpoint(Resource):
    """
    Endpoint to control emulation.
    """
    def post(self):
        """
        Start emulation.
        """
        LOG.info("POST /emulation")
        if app.emulation_process is not None:
            return "Conflict: Emulation already running", 409
        # spawn new process for the emulator
        # see: https://docs.python.org/3/library/multiprocessing.html
        # see: https://docs.python.org/2.7/library/multiprocessing.html
        # ctx = multiprocessing.get_context('spawn')
        app.emulation_process_queue = mp.Queue()
        app.emulation_process_running = mp.Value(c_bool, True)
        app.emulation_process = mp.Process(
            target=start_emulation,
            args=(app.emulation_process_queue,
                  app.emulation_process_running,
                  app.cliargs, ))  # (arg1,)
        app.emulation_process.start()
        return True, 201

    def delete(self):
        """
        Stop emulation.
        """
        LOG.info("DELETE /emulation")
        if app.emulation_process is None:
            return "Not found: No emulation running?", 403
        stop_emulation()
        return True, 200

    def get(self):
        """
        Return status
        """
        LOG.info("GET /emulation")
        return app.emulation_process is not None, 200


def start_emulation(ipc_queue, ipc_running, cliargs):
    t = EmulatorProfilingTopology(cliargs)
    t.start()
    print("{} Emulation running ..."
          .format(datetime.datetime.now()))
    # run until emulation is stopped
    while(True):
        time.sleep(1)
        # print("Emulation running ...")
        if not ipc_queue.empty():
            if ipc_queue.get() == "stop":
                print("Emulation process received: 'stop'")
                break
    t.stop()
    ipc_running.value = False
    LOG.debug("Set emulation_process_running = False")


def stop_emulation():
    if app.emulation_process is not None:
        app.emulation_process_queue.put("stop")
        LOG.debug("Sent stop signal to emulation process")
        while app.emulation_process_running.value:
            LOG.info("Waiting for emulation to stop ...")
            time.sleep(1)
        app.emulation_process.join()
        app.emulation_process = None


class EmulatorProfilingTopology(object):

    def __init__(self, args):
        self.args = args

    def start(self):
        LOG.info("Starting emulation ...")
        LOG.info("Args: {}".format(self.args))
        setLogLevel('info')  # set Mininet loglevel
        # create topology
        self.net = DCNetwork(monitor=False,
                             enable_learning=self.args.learning)
        # we only need one DC for benchmarking
        dc = self.net.addDatacenter("dc1")
        # add the command line interface endpoint to each DC (REST API)
        self.rapi1 = RestApiEndpoint("0.0.0.0", 5001)
        self.rapi1.connectDCNetwork(self.net)
        self.rapi1.connectDatacenter(dc)
        self.rapi1.start()
        # add the 5GTANGO lightweight life cycle manager (LLCM) to the topology
        self.llcm1 = TangoLLCMEndpoint("0.0.0.0", 5000, deploy_sap=False)
        self.llcm1.connectDatacenter(dc)
        self.llcm1.start()
        self.net.start()

    def stop(self):
        LOG.info("Stopping emulation ...")
        self.rapi1.stop()
        self.llcm1.stop()
        self.net.stop()
