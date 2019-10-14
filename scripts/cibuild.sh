#!/usr/bin/env bash

set -e -x

docker build -t "cli-builder:${BUILD_TAG}" .

docker run \
    --rm \
    -e USER=${USER} \
    -e USERID=$(grep Uid /proc/self/status | cut -f2 | awk '{$1=$1};1') \
    -u $(id -u) \
    -v $(pwd):/src \
    "cli-builder:${BUILD_TAG}"
