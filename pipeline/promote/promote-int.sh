#!/bin/bash
set -e
docker tag registry.sonata-nfv.eu:5000/tng-sdk-benchmark:latest registry.sonata-nfv.eu:5000/tng-sdk-benchmark:int
docker push registry.sonata-nfv.eu:5000/tng-sdk-benchmark:int
