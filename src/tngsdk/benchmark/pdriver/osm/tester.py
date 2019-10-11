from tngsdk.benchmark.pdriver.osm.conn_mgr import OSMConnectionManager
from pprint import pprint
from osmclient import client
from osmclient.common.exceptions import ClientException
import yaml
from prettytable import PrettyTable
import tarfile
from io import StringIO, BytesIO
import time

def vnfd_update(vnfd):
    """
    Implement VNFD updater here
    """
    vnfd['vnfd:vnfd-catalog']['vnfd'][0]['version'] = '2.5'
    return vnfd


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
myclient.vnfd.create("hackfest_cloudinit_vnf.tar.gz")

# Begin tar.gzip yaml extractor
# Haydar

tarf = tarfile.open("hackfest_cloudinit_vnf.tar.gz",'r:gz')
members = tarf.getmembers()
new_tar = tarfile.open("new_vnfd.tar.gz", "w:gz")

print("opened tar.gz archive")

for member in members:
    member_name = member.name
    if member_name.endswith(".yaml") or member_name.endswith(".yml"):
        member_contents = tarf.extractfile(member)
        vnfd_contents = yaml.safe_load(member_contents)
        new_vnfd = vnfd_update(vnfd_contents)
        new_vnfd_ti = tarfile.TarInfo(member_name)
        new_vnfd_stream = yaml.dump(new_vnfd).encode('utf8')
        new_vnfd_ti.size = len(new_vnfd_stream)
        vnf_size = new_vnfd_ti.size
        buffer = BytesIO(new_vnfd_stream)
        new_tar.addfile(tarinfo=new_vnfd_ti, fileobj=buffer)
        print('done writing vnfd to new archive')
    else:
        new_tar.addfile(member, tarf.extractfile(member))

new_tar.close()
print("new archive created")
    

# print("Sleeping!")
# time.sleep(15)

# New client needs to be created to actually update VNF, so weird! 
myclient = client.Client(host=hostname, sol005=True, **kwargs)
vnfd_name = myclient.vnfd.get("hackfest_cloudinit-vnf")
print(vnfd_name)
vnfd_updated = myclient.vnfd.update("hackfest_cloudinit-vnf", "new_vnfd.tar.gz")
