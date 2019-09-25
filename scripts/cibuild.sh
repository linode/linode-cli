#!/usr/bin/env bash

set -x

docker build -t linode-cli-$BUILD_TAG .

docker run \
    --rm \
    -e USER=${USER} \
    -e USERID=$(grep Uid /proc/self/status | cut -f2 | awk '{$1=$1};1') \
    -u $(id -u) \
    -v $(pwd)/dist:/src/dist \
    linode-cli-$BUILD_TAG
