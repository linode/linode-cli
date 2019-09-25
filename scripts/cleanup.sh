#!/usr/bin/env bash

set -x

# Cleanup the docker image
docker rmi linode-cli-$BUILD_TAG linode-cli-test
