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
import os
import pandas as pd
from flatten_dict import flatten
from tngsdk.benchmark.logger import TangoLogger
from tngsdk.benchmark.helper import read_json, read_yaml
from tngsdk.benchmark.helper import dubunderscore_reducer


LOG = TangoLogger.getLogger(__name__)


PATH_EX_CONFIG = "ex_config.json"
PATH_CONTAINER_MONITORING = "cmon.json"
PATH_CONTAINER_RESULT = "tngbench_share/result.yml"

PATH_OUTPUT_EC_METRICS = "result_ec_metrics.csv"
PATH_OUTPUT_TS_METRICS = "result_ts_metrics.csv"


class VimemuResultProcessor(object):

    def __init__(self, args, service_experiments):
        self.args = args
        self.result_dir = args.result_dir
        self.service_experiments = service_experiments

    def run(self):
        if not os.path.exists(self.result_dir):
            LOG.info("Result dir '{}' does not exist. Skipping"
                     .format(self.result_dir))
            return
        # FIXME support multipe experiments in a single result folder
        # gen. list of result folder per experiment run
        rdlist = sorted([os.path.join(self.result_dir, rd)
                        for rd in os.listdir(self.result_dir)
                        if os.path.isdir(os.path.join(self.result_dir, rd))])
        # read experiment metrics
        df_em = self.read_experiment_metrics(rdlist)
        # read timeseries metrics
        df_tm = self.read_timeseries_metrics(rdlist)
        df_em.info()
        df_tm.info()
        # store the data frames
        df_em.to_csv(os.path.join(self.result_dir, PATH_OUTPUT_EC_METRICS))
        df_tm.to_csv(os.path.join(self.result_dir, PATH_OUTPUT_TS_METRICS))

    def read_experiment_metrics(self, rdlist):
        """
        return pandas
        """
        rows = list()
        for idx, rd in enumerate(rdlist):
            LOG.info("Processing experiment metrics {}/{}"
                     .format(idx + 1, len(rdlist)))
            row = dict()
            try:
                # collect data from different sources
                row.update(self._collect_ecs(rd))
                row.update(self._collect_container_results(rd))
            except FileNotFoundError as ex:
                LOG.error("Result corrupted: {}".format(ex))
            rows.append(row)
        # to Pandas
        return pd.DataFrame(rows)

    def read_timeseries_metrics(self, rdlist):
        """
        return pandas
        """
        rows = list()
        for idx, rd in enumerate(rdlist):
            LOG.info("Processing timeseries metrics {}/{}"
                     .format(idx + 1, len(rdlist)))
            try:
                rows.extend(self._collect_ts_container_monitoring(rd))
            except FileNotFoundError as ex:
                LOG.error("Result corrupted: {}".format(ex))
        # to Pandas
        return pd.DataFrame(rows)

    def _collect_ecs(self, rd):
        """
        Collect ECs from 'PATH_EX_CONFIG'
        """
        r = dict()
        jo = read_json(os.path.join(rd, PATH_EX_CONFIG))
        r["run_id"] = jo.get("run_id", -1)
        r["experiment_name"] = jo.get("name")
        if "parameter" in jo:
            for k, v in jo.get("parameter").items():
                # clean up the parameter keys
                k = k.replace("ep::", "param::")
                k = k.replace("function", "func")
                k = k.replace("::", "__")
                r[k] = v
        return r

    def _collect_container_results(self, rd):
        """
        Collect ECs from '<container_name>/PATH_CONTAINER_RESULT'
        """
        r = dict()
        # iterate over all container directories
        for cd in self._get_container_from_rd(rd):
            yml = read_yaml(os.path.join(rd, cd, PATH_CONTAINER_RESULT))
            for k, v in yml.items():
                # add container name as key prefix
                k = "metric__{}__{}".format(self._get_clean_cname(cd), k)
                r[k] = v
        return r

    def _collect_ts_container_monitoring(self, rd):
        """
        Collect time series data from 'PATH_CONTAINER_MONITORING'
        Data: list of tuples(timestamp, dict(docker stats))
        Returns list of rows
        """
        samples = read_json(os.path.join(rd, PATH_CONTAINER_MONITORING))
        rows = list()
        min_time = min([ts for (ts, smpl) in samples])
        for (ts, smpl) in samples:
            row = dict()
            row["timestamp"] = ts - min_time
            row.update(self._flat_sample(smpl))
            rows.append(row)
        return rows

    def _get_container_from_rd(self, rd):
        return sorted([cd for cd in os.listdir(rd)
                       if os.path.isdir(os.path.join(rd, cd))
                       and "mn." in cd])

    def _get_clean_cname(self, name):
        return name.replace("mn.", "").strip(".-/_ ")

    def _flat_sample(self, smpl):
        """
        Make a flat dict from given multi-dim smpl dict.
        """
        r = dict()
        for cname, data in smpl.items():
            r["cname"] = cname
            r.update(flatten(data, reducer=dubunderscore_reducer))
        return r
