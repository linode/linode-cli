#!/usr/bin/env bash

docker run \
    --entrypoint "" \
    --rm \
    -v $(pwd):/src \
    linode-cli \
    twine upload -u "${pypi_user}" -p "${pypi_password}" "/src/dist/*.whl"
