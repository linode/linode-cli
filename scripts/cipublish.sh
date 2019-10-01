#!/usr/bin/env bash

set -e -x

docker run \
    --entrypoint "" \
    --rm \
    -e USER=${USER} \
    -e USERID=$(grep Uid /proc/self/status | cut -f2 | awk '{$1=$1};1') \
    -u $(id -u) \
    -v $(pwd):/src \
    linode-cli-$BUILD_TAG \
    twine upload -u "${pypi_user}" -p "${pypi_password}" "/src/dist/*.whl"
