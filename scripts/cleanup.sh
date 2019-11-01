#!/usr/bin/env bash

set -e -x

# Cleanup the docker image
docker rmi cli-builder:${BUILD_TAG} linode-cli-test
