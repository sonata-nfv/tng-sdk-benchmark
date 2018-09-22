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
import sys
import argparse
import coloredlogs
from flask import Flask, Blueprint
from flask_restplus import Resource, Api, Namespace
from werkzeug.contrib.fixers import ProxyFix


LOG = logging.getLogger(os.path.basename(__file__))


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
api.add_namespace(api_v1)


def serve_forever(args, debug=True):
    """
    Start REST API server. Blocks.
    """
    # TODO replace this with WSGIServer for better performance
    app.cliargs = args
    app.run(host=args.service_address,
            port=args.service_port,
            debug=debug)


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
    serve_forever(args)


@api_v1.route("/emulation")
class EmulationEndpoint(Resource):
    """
    Endpoint to control emulation.
    """
    def post(self):
        LOG.warning("POST endpoint not implemented yet")
        return "not implemented", 501

    def delete(self):
        LOG.warning("DELETE endpoint not implemented yet")
        return "not implemented", 501
