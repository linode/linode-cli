#!/bin/bash

# Get an available image and set it as an env variable
if [ -z "$test_image" ]; then
    export test_image=$(linode-cli images list --format id --text --no-header | egrep "linode\/.*" | head -n 1)
fi

# Random pass to use persistently thorough test run
if [  -z "$random_pass" ]; then
    export random_pass=$(openssl rand -base64 32)
fi

# A Unique tag to use in tag related tests
if [ -z "$uniqueTag" ]; then
    export uniqueTag="$(date +%s)-tag"
fi

createLinode() {
    local linode_type=$(linode-cli linodes types --text --no-headers --format="id" | xargs | awk '{ print $1 }')
    local test_image=$(linode-cli images list --format id --text --no-header | egrep "linode\/.*" | head -n 1)
    local random_pass=$(openssl rand -base64 32)
    run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli linodes create --type=$linode_type --region us-east --image=$test_image --root_pass=$random_pass"

    assert_success
}

createVolume() {
    timestamp=$(date +%s)
    run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli volumes create --label=A$timestamp --size=10 --region=us-east"
    assert_success
}

shutdownLinodes() {
    local linode_ids="( $(LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli --text --no-headers linodes list | awk '{ print $1 }' | xargs) )"
    local id

    for id in $linode_ids ; do
        run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli linodes shutdown $id"
    done
}

removeLinodes() {
    local linode_ids="( $(LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli --text --no-headers linodes list | awk '{ print $1 }' | xargs) )"
    local id

    for id in $linode_ids ; do
        run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli linodes delete $id"
    done
}

removeDomains() {
    local domain_ids="( $( linode-cli domains list --format "id" --text --no-headers ) )"
    local id

    for id in $domain_ids ; do
        run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli domains delete $id"
        [ "$status" -eq 0 ]
    done
}

removeVolumes() {
    local volume_ids="( $(linode-cli volumes list --text --no-headers --format="id" | xargs) )"
    local id

    for id in $volume_ids ; do
        run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli volumes delete $id"
    done
}

removeAll() {
    local entity_ids="( $(linode-cli $1 list --text --no-headers --format="id" | xargs) )"
    local id

    for id in $entity_ids ; do
        run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli $1 delete $id"
    done
}

removeUniqueTag() {
    run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli tags delete $uniqueTag"
}

createLinodeAndWait() {
    local default_plan=$(linode-cli linodes types --text --no-headers --format="id" | xargs | awk '{ print $1 }')
    local linode_type=${1:-$default_plan}

    run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli linodes create --type=$linode_type --region us-east --image=$test_image --root_pass=$random_pass"
    assert_success

    local linode_id=$(LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli linodes list --format id --text --no-header | head -n 1)

    SECONDS=0
    until [ $(LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]; do
        echo 'still provisioning'
        sleep 5 # Wait 5 seconds before checking status again, to rate-limit ourselves
        if (( $SECONDS > 180 )); then
            echo "Failed to provision.. Failed after $SECONDS seconds" >&3
            assert_failure # Fail test, linode did not boot in time
            break
        fi
    done
}


setToken() {
    source ./.env

    if [[ "$TOKEN_1_IN_USE_BY" = "NONE" && "$TOKEN_2_IN_USE_BY" != $1 ]]; then
        export LINODE_CLI_TOKEN=$TOKEN_1
        export TOKEN_1_IN_USE_BY=$1
    elif [[ "$TOKEN_1_IN_USE_BY" != $1 && "$TOKEN_1_IN_USE_BY" != "NONE" && "$TOKEN_2_IN_USE_BY" = "NONE" ]]; then
        export LINODE_CLI_TOKEN=$TOKEN_2
        export TOKEN_2_IN_USE_BY=$1
    elif [ "$TOKEN_1_IN_USE_BY" = $1 ]; then
        export LINODE_CLI_TOKEN=$TOKEN_1
    elif [ "$TOKEN_2_IN_USE_BY" = $1 ]; then
        export LINODE_CLI_TOKEN=$TOKEN_2
    fi

    run bash -c "echo -e \"export TOKEN_1=$TOKEN_1\nexport TOKEN_2=$TOKEN_2\nexport TOKEN_1_IN_USE_BY=$TOKEN_1_IN_USE_BY\nexport TOKEN_2_IN_USE_BY=$TOKEN_2_IN_USE_BY\" > ./.env"
}

clearToken() {
    source ./.env

    if [ "$TOKEN_1_IN_USE_BY" = $1 ]; then
        export TOKEN_1_IN_USE_BY=NONE
    elif [ "$TOKEN_2_IN_USE_BY" = $1 ]; then
        export TOKEN_2_IN_USE_BY=NONE
    fi

    unset LINODE_CLI_TOKEN

    run bash -c "echo -e \"export TOKEN_1=$TOKEN_1\nexport TOKEN_2=$TOKEN_2\nexport TOKEN_1_IN_USE_BY=$TOKEN_1_IN_USE_BY\nexport TOKEN_2_IN_USE_BY=$TOKEN_2_IN_USE_BY\" > ./.env"
}
