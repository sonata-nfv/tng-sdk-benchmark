#!/bin/bash
set -e
docker build --no-cache -t registry.sonata-nfv.eu:5000/tng-sdk-benchmark .
