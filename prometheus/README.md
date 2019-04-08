# Use Prometheus to monitor the experiment exectuors, containers, etc.

## Installations & Run

### Prmetheus Node (Controller machine runing tng-bench)

```
docker-compose up
```

### Executor Node (Executor machine running vim-emu)
#### Host metric collector

Uses the [node exporter](https://github.com/prometheus/node_exporter) to collect statistics from the executor machine on which vim-emu runs.

Install
```
wget https://github.com/prometheus/node_exporter/releases/download/v0.17.0/node_exporter-0.17.0.linux-amd64.tar.gz
tar xvfz node_exporter-*.*-amd64.tar.gz
sudo ufw allow 9100
```

Run
```
cd node_exporter-*.*-amd64
./node_exporter
```

Aleternatively as Docker (some metrics might have problems):
```
sudo docker run -d \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  --publish=9100:9100 \
  --name=nodeexporter \
  quay.io/prometheus/node-exporter \
  --path.rootfs /host
  ```
  
Example metric:

```
rate(node_cpu_seconds_total[1m])
```

#### Docker Collector (Docker daemon)

**Just for completeness. Seem to be of limited values, i.e., no helpful metrics are exposed. Can be skipped!**

See [this tutorial](https://docs.docker.com/config/thirdparty/prometheus/) for more info.

Reconfigure Docker config: `/etc/docker/daemon.json`

```
{
  "metrics-addr" : "0.0.0.0:9101",
  "experimental" : true
}
```

And `sudo ufw allow 9101`

#### Docker Collector (cAdvisor)

Run (runs in background)
```
sudo docker run \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --volume=/dev/disk/:/dev/disk:ro \
  --publish=9102:8080 \
  --detach=true \
  --name=cadvisor \
  google/cadvisor:latest
```

It gives very many metrics. Filter my a container name, e.g., `mn.vnf0.vdu01` works like:

```
rate(container_cpu_usage_seconds_total{name="mn.vnf0.vdu01"}[1m])
```

#### VNF-specific collectors

Only if VNFs support it. Expose ports vnf0: `9110`, vnf1: `9111`, ... etc.

See suricata example.

Example metrics:

```
rate(suricata_stats_capture_kernel_packets[1m])
```

#### Probe-specific collectors

Not yet implemented.

## Data

Prometheus data will be stored in folder  `prometheus-data` in this folder.