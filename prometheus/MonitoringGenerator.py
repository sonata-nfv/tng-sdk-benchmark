import yaml
import os
import sys
import pprint

pp = pprint.PrettyPrinter(width=41, compact=True)


class PrometheusGen():
    """ Generate monitoring configuration for prometheus """

    def __init__(self):
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
        self.add_global_config()
        pp.pprint(self.result)

    def new_static_job(self, job):
        """
        @job - dictionary
        {@name - string, @targets - list or string }
        """
        job_conf = {
            "job_name": job.name,
            "static_configs": [
                    { "targets": job.targets }
                ]
        }
        self.result["scrape_configs"].append(job_conf)

    def load_file(self, file_path):
        with open(file_path, 'r') as stream:
            try:
                contents = yaml.safe_load(stream)
                return contents
            except yaml.YAMLError as exc:
                print(exc)

    def add_static_host(self, ip):
        pass

    def add_openstack_dynamic_monitoring(self, openstack_object):
        pass

    def write_file(self, filename):
        pass

if __name__ == '__main__':
    # file = '/home/avi/REPO/tng-sdk-benchmark/prometheus/prometheus.yml'
    config = PrometheusGen()
    config.generate()
    # config.new_static_job()
    # pp.pprint(config.file_contents)