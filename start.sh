#!/bin/bash

# AUTHOR  : avimehenwal
# DATE    : 16th-Sep-2019
# PURPOSE : Quickly build and launch tng-bench commandline 


IMG_NAME="avi/tng-bench"

if [ `basename $PWD` == "tng-sdk-benchmark" ]
then
    docker build --tag $IMG_NAME .
    # --rm Do not remove the docker for debugging and logging purposes
    docker run \
        --interactive --tty \
        --volume `pwd`:/tng-sdk-benchmark \
        $IMG_NAME
fi

CONTAINER_ID=`docker ps --all | grep avi/tng-bench | awk '{print$1}'`
echo -e "INFO: Container ID -> $CONTAINER_ID"