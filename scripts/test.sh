#!/usr/bin/env bash

set -e -x

docker build \
  -f Dockerfile-bats \
  --build-arg API_OVERRIDE="${API_OVERRIDE}" \
  --build-arg SPEC="${SPEC}" \
  -t linode-cli-test .

docker run \
    -e TOKEN_1="${TOKEN_1}" \
    -e TOKEN_2="${TOKEN_2}" \
    -e TEST_ENVIRONMENT="${ENVIRONMENT}" \
    -e DOCKER_BATS="TRUE" \
    -e RUN_LONG_TESTS="${LONG_TESTS}" \
    -v $SSH_PRIVATE_KEY:/root/.ssh/id_rsa \
    -v $SSH_PUBLIC_KEY:/root/.ssh/id_rsa.pub \
    --rm \
    linode-cli-test
