#!/usr/bin/env bash

docker build -t linode-cli-$BUILD_TAG .

docker run --rm -e USER=${USER} -e USERID=${USERID} -u ${USERID} -v $(pwd)/dist:/src/dist linode-cli-$BUILD_TAG
