#!/usr/bin/env bash

# Cleanup the docker image
docker rmi linode-cli-$BUILD_TAG
docker rmi linode-cli-test