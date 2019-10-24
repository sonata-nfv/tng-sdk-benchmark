import paramiko

"""
Must install paramiko first
"""

vnf_ip = "172.24.4.109"
vnf_username = "cirros"
vnf_password = "gocubsgo"
vnf_cmd = "echo 'hello'"
vnf_data_ip = "172.24.4.109"

probe_ip = "172.24.4.179"
probe_username = "cirros"
probe_password = "gocubsgo"
probe_cmd = f"./start.sh {vnf_data_ip}"


# Init vnf
vnf_ssh_client = paramiko.SSHClient()
vnf_ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
vnf_ssh_client.connect(vnf_ip, username=vnf_username, password=vnf_password)
vnf_stdin, vnf_stdout, vnf_stderr = vnf_ssh_client.exec_command(vnf_cmd)
print("VNF: ", vnf_stdout.readlines())
print(type(vnf_stdout.readlines()))


# Init probe
probe_ssh_client = paramiko.SSHClient()
probe_ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
probe_ssh_client.connect(probe_ip, username=probe_username, password=probe_password)
probe_stdin, probe_stdout, probe_stderr = probe_ssh_client.exec_command(probe_cmd)
print("Probe: ", probe_stdout.readlines())
print(type(probe_stdout.readlines()))
