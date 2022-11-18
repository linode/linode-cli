#!/usr/bin/env bash

set -e

export LINODE_CLI_TOKEN=$1

CLEAN_TARGETS=( linodes volumes domains nodebalancers stackscripts images lke)

for i in "${CLEAN_TARGETS[@]}"; do
    deleteCmd="delete"

    if [ "${i}" = "stackscripts" ] || [ "${i}" = "images" ]; then
        ENTITIES=( $(linode-cli "${i}" list --is_public false --text --no-headers --format "id,tags" --delimiter " " | grep -v "linuke-keep" | awk '{ print $1 }' | xargs) )
    elif [ "${i}" == "lke" ]; then
        ENTITIES=( $(linode-cli "${i}" clusters-list --text --no-headers --format "id,tags" --delimiter " " | grep -v "linuke-keep" | awk '{ print $1 }' | xargs) )
        deleteCmd="cluster-delete"
    else
        ENTITIES=( $(linode-cli "${i}" list --text --no-headers --format "id,tags" --delimiter " " | grep -v "linuke-keep" | awk '{ print $1 }' | xargs) )
    fi

    declare ENTITIES

    if [ ${#ENTITIES[@]}  != "0" ]; then
        for id in "${ENTITIES[@]}"; do
            linode-cli "${i}" "${deleteCmd}" "${id}"
        done
    fi
done

unset LINODE_CLI_TOKEN
