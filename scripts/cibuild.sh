#!/usr/bin/env bash

docker build -t linode-cli-$BUILD_TAG .

docker run --rm -v $(pwd)/dist:/src/dist linode-cli-$BUILD_TAG
