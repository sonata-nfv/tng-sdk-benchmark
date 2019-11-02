import yaml
import os
import sys
import pprint

pp = pprint.PrettyPrinter(width=41, compact=True)


class PrometheusGen():
    """ Generate monitoring configuration for prometheus """

    def __init__(self):
    # def __init__(self, file_path):
        # self.file_path = file_path
        # self.file_contents = self.load_file(self.file_path)
        self.default_scrape_interval = '2s'
        self.evaluation_interval = "1m"
        
        self.result = {
            "global" : {},
            "scrape_configs" : [] 
        }

    def add_global_config(self):
        self.prometheus_global = {
            "scrape_interval": self.default_scrape_interval,
            "evaluation_interval": self.evaluation_interval,
        }
        self.result["global"] = self.prometheus_global 

    def generate(self):
        """
        todo - write to a file
        """
        self.add_global_config()
        pp.pprint(self.result)

    def add_static_job(self, job):
        """
        @job - dictionary
        {@name - string, @targets - list or string }
        """
        job_conf = {
            "job_name": job["name"],
            "static_configs": [
                    { "targets": job["targets"] }
                ]
        }
        pp.pprint(job_conf)
        self.result["scrape_configs"].append(job_conf)

    def load_file(self, file_path):
        with open(file_path, 'r') as stream:
            try:
                contents = yaml.safe_load(stream)
                return contents
            except yaml.YAMLError as exc:
                print(exc)

    def add_openstack_dynamic_monitoring(self):
        """
        Dynamic openstack monitoring querying nova API
        todo - use openstack infor from tng-bench
        """
    # - job_name: 'openstack'
    #     openstack_sd_configs:
    #   - identity_endpoint: http://fgcn-of-2.cs.upb.de/horizon/identity
    #     username: admin
    #     project_name: admin
    #     password: ADMIN_PASS
    #     role: instance
    #     region: RegionOne
    #     domain_name: Default
        job_config = {
            "job_name": "openstack",
            "openstack_sd_configs": [
                {
                    "identity_endpoint": "http://fgcn-backflip9.cs.uni-paderborn.de/identity",
                    "password": "admin",
                    "username": "admin",
                    "project_name": "admin",
                    "region": "RegionOne",
                    "role": "instance"
                }
            ],
            "relabel_configs": [
                {
                    'action': 'keep',
                    'regex': 'ACTIVE',
                    'source_labels': ['__meta_openstack_instance_status']
                }
            ]
        }
        pp.pprint(job_config)
        self.result["scrape_configs"].append(job_config)


    def write_file(self, filename):
        pass

if __name__ == '__main__':
    file = '/home/avi/REPO/tng-sdk-benchmark/prometheus/prometheus.yml'
    vnf1 = {
        "name": "vnf1",
        "targets": "192.169.1.10"
    }
    vnf2 = {
        "name": "2-vnfs",
        "targets": ["192.169.1.12", "192.169.1.11"]
    }
    openstack = {
        ""
    }

    # TEST
    config = PrometheusGen()
    # config = PrometheusGen(file)
    config.add_static_job(vnf1)
    config.add_static_job(vnf2)
    config.add_openstack_dynamic_monitoring()
    config.generate()
    # pp.pprint(config.file_contents)