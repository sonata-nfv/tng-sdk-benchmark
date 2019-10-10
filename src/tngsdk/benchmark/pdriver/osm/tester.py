from tngsdk.benchmark.pdriver.osm.conn_mgr import OSMConnectionManager
from pprint import pprint
from osmclient import client
from osmclient.common.exceptions import ClientException
import yaml
from prettytable import PrettyTable

hostname = "fgcn-backflip3.cs.upb.de"
user = "admin"
password = "admin"
project = "admin"
kwargs = {}

if user is not None:
    kwargs['user']=user
if password is not None:
    kwargs['password']=password
if project is not None:
   kwargs['project']=project
myclient = client.Client(host=hostname, sol005=True, **kwargs)

resp = myclient.vnfd.list()
print(yaml.safe_dump(resp))


# config = {
#     "osm_host": "fgcn-backflip3.cs.upb.de",
#     "osm_port": "9999",
#     "username": "admin",
#     "password": "admin",
#     "project_id": "6edb5643-bc69-4c9d-8623-b4eee539a458"
# }

# conn_mgr = OSMConnectionManager(config)

# conn_mgr.connect()

# pprint(conn_mgr.upload_vnfd("hackfest_cloudinit_vnf.tar.gz"))