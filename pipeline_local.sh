#!/bin/bash
set -e
# Helper script that runs parts of the CI/CD pipeline locally.
# Can be used to check code before pushing.

# check style early
flake8 --exclude .eggs,venv,build,src/tngsdk/benchmark/ietf/vnf_bd.py
# local test
pytest -v
# build container
pipeline/build/build.sh
# run tests
pipeline/unittest/test.sh
# run codestyle
pipeline/checkstyle/check.sh
