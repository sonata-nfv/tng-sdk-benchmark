from tngsdk.benchmark.pdriver.osm.conn_mgr import OSMConnectionManager
from pprint import pprint
from osmclient import client
from osmclient.common.exceptions import ClientException
import yaml
from prettytable import PrettyTable
import tarfile
from io import StringIO, BytesIO
import time
from tngsdk.benchmark.helper import write_yaml



# def vnfd_update(vnfd):
#     """
#     Implement VNFD updater here
#     """
#     temp_config = {}
#     temp_config['specification'] = {}
#     temp_config['specification']['memory-mb'] = 1024
#     temp_config['specification']['storage-gb'] = 5
#     temp_config['specification']['vcpu-count'] = 2

#     vnfd['vnfd:vnfd-catalog']['vnfd'][0]['version'] = '2.5'
#     vnfd['vnfd:vnfd-catalog']['vnfd'][0]['vdu'][0]['vm-flavor'] = {
#         'memory-mb': temp_config['specification']['memory-mb'],
#         'storage-gb': temp_config['specification']['storage-gb'],
#         'vcpu-count': temp_config['specification']['vcpu-count']}
#     # print("Type of vnfd in fn: ",type(vnfd),sep=' ')
#     # print(vnfd)

#     return vnfd


hostname = "fgcn-backflip3.cs.upb.de"
user = "admin"
password = "admin"
project = "admin"
kwargs = {}

if user is not None:
    kwargs['user'] = user
if password is not None:
    kwargs['password'] = password
if project is not None:
    kwargs['project'] = project
myclient = client.Client(host=hostname, sol005=True, **kwargs)
# myclient.vnfd.create("/home/bhuvan/tng-sdk-benchmark/examples-osm/services/example-ns-1vnf-any/example_vnf.tar.gz")
# # myclient.vnfd.create("hackfest_cloudinit_vnf.tar.gz")
# # Begin tar.gzip yaml extractor
# # Haydar

# tarf = tarfile.open(
#     "/home/bhuvan/tng-sdk-benchmark/examples-osm/services/example-ns-1vnf-any/example_vnf.tar.gz", 'r:gz')
# # tarf = tarfile.open("hackfest_cloudinit_vnf.tar.gz",'r:gz')
# members = tarf.getmembers()
# new_tar = tarfile.open("new_vnfd.tar.gz", "w:gz")

# print("opened tar.gz archive")

# for member in members:
#     member_name = member.name
#     if member_name.endswith(".yaml") or member_name.endswith(".yml"):
#         member_contents = tarf.extractfile(member)
#         vnfd_contents = yaml.safe_load(member_contents)
#         new_vnfd_contents = vnfd_update(vnfd_contents)
#         new_vnfd_ti = tarfile.TarInfo(member_name)
#         new_vnfd_stream = yaml.dump(new_vnfd_contents).encode('utf8')
#         new_vnfd_ti.size = len(new_vnfd_stream)
#         vnf_size = new_vnfd_ti.size
#         buffer = BytesIO(new_vnfd_stream)
#         new_tar.addfile(tarinfo=new_vnfd_ti, fileobj=buffer)
#         print('done writing vnfd to new archive')
#     else:
#         new_tar.addfile(member, tarf.extractfile(member))

# new_tar.close()
# print("new archive created")


# # print("Sleeping!")
# # time.sleep(5)

# # New client needs to be created to actually update VNF, so weird!
# myclient = client.Client(host=hostname, sol005=True, **kwargs)
# vnfd_name = myclient.vnfd.get("example_vnf")
# # print(vnfd_name)
# # pprint.pprint(vnfd_name)
# # print(type(vnfd_name))
# vnfd_updated = myclient.vnfd.update("example_vnf", "new_vnfd.tar.gz")
vim_access={}
vim_access['vim-type'] = "openstack"
vim_access['description'] = "description"
vim_access['vim-url'] = "http://fgcn-backflip9.cs.upb.de/identity/v3"
vim_access['vim-username'] = "admin"
vim_access['vim-password'] = "admin"
vim_access['vim-tenant-name'] = "admin"

vim_config = {"use_floating_ip":True}        
write_yaml('/tmp/temp_vim_config.yaml', vim_config)
# with open(r'/tmp/temp_vim_config.yaml', 'w') as file:
#     documents = yaml.dump(vim_config, file)
vim_access['config']=open(r'/tmp/temp_vim_config.yaml')

myclient.vim.create("trial_vim", vim_access,wait=True)


myclient.vim.delete("trial_vim")

