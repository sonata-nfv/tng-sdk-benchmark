#!/bin/bash

# AUTHOR  : avimehenwal
# DATE    : 16th-Sep-2019
# PURPOSE : Quickly build and launch tng-bench commandline 


IMG_NAME="avi/tng-bench"

if [ `basename $PWD` == "tng-sdk-benchmark" ]
then
    docker build --tag $IMG_NAME .
    docker run \
        --interactive --rm --tty \
        --volume `pwd`:/tng-sdk-benchmark \
        $IMG_NAME
fi