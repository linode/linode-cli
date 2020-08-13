#!/usr/bin/env bash

set -e

export LINODE_CLI_TOKEN=$1

CLEAN_TARGETS=( linodes volumes domains nodebalancers stackscripts images)

for i in "${CLEAN_TARGETS[@]}"; do
    ENTITIES=( $(linode-cli "${i}" list --text --no-headers --format "id" --delimiter " ") )

    if [ "${i}" = "stackscripts" ] || [ "${i}" = "images" ]; then
        ENTITIES=( $(linode-cli "${i}" list --is_public false --text --no-headers --format "id" --delimiter " ") )
    fi

    declare ENTITIES

    if [ ${#ENTITIES[@]}  != "0" ]; then
        for id in "${ENTITIES[@]}"; do
            linode-cli "${i}" delete "${id}"
        done
    fi
done

unset LINODE_CLI_TOKEN
