from tngsdk.benchmark.pdriver.osm.conn_mgr import OSMConnectionManager
from pprint import pprint

config = {
    "osm_host": "fgcn-backflip3.cs.upb.de",
    "osm_port": "9999",
    "username": "admin",
    "password": "admin",
    "project_id": "6edb5643-bc69-4c9d-8623-b4eee539a458"
}

conn_mgr = OSMConnectionManager(config)

conn_mgr.connect()

pprint(conn_mgr.upload_vnfd("hackfest_cloudinit_vnf.tar.gz"))