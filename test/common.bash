#!/usr/bin/env bash

# Get an available image and set it as an env variable
if [ -z "$test_image" ]; then
    export test_image=$(linode-cli images list --format id --text --no-header | egrep "linode\/.*" | head -n 1)
fi

# Random pass to use persistently thorough test run
if [ -z "$random_pass" ]; then
    export random_pass=$(openssl rand -base64 32)
fi

# A Unique tag to use in tag related tests
if [ -z "$uniqueTag" ]; then
    export uniqueTag="$(date +%s)-tag"
fi
#
# A Unique user to use in user related tests
if [ -z "$uniqueUser" ]; then
    export uniqueUser="test-user-$(date +%s)"
fi

createLinode() {
    local region=${1:-us-east}
    local linode_type=$(linode-cli linodes types --text --no-headers --format="id" | xargs | awk '{ print $1 }')
    local test_image=$(linode-cli images list --format id --text --no-header | egrep "linode\/.*" | head -n 1)
    local random_pass=$(openssl rand -base64 32)
    run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli linodes create --type=$linode_type --region $region --image=$test_image --root_pass=$random_pass"

    assert_success
}

createDomain() {
    timestamp=$(date +%s)

    run linode-cli domains create \
        --type master \
        --domain "A$timestamp-example.com" \
        --soa_email="developer-test@linode.com" \
        --text \
        --no-header \
        --delimiter ","

    assert_success
    assert_output --regexp "[0-9]+,A[0-9]+-example.com,master,active,developer-test@linode.com"
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

removeLkeClusters() {
    local cluster_ids="( $(LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli --text --no-headers lke clusters-list | awk '{ print $1 }' | xargs) )"
    local id

    for id in $cluster_ids ; do
        run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli lke cluster-delete $id"
    done
}

removeAll() {
    if [ "$1" = "stackscripts" ]; then
        entity_ids="( $(linode-cli $1 list --is_public=false --text --no-headers --format="id" | xargs) )"
    else
        entity_ids="( $(linode-cli $1 list --text --no-headers --format="id" | xargs) )"
    fi

    local id

    for id in $entity_ids ; do
        run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli $1 delete $id"
    done
}

removeTag() {
    run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli tags delete $1"
}

createLinodeAndWait() {
    local test_image=$(linode-cli images list --format id --text --no-header | egrep "linode\/.*" | head -n 1)
    local default_plan=$(linode-cli linodes types --text --no-headers --format="id" | xargs | awk '{ print $1 }')
    local linode_image=${1:-$test_image}
    local linode_type=${2:-$default_plan}

    # $3 is ssh-keys
    if [ -n "$3" ]; then
        run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli linodes create --type=$linode_type --region us-east --image=$linode_image --root_pass=$random_pass --authorized_keys=\"$3\""
        assert_success
    else
        run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli linodes create --type=$linode_type --region us-east --image=$linode_image --root_pass=$random_pass"
        assert_success
    fi

    local linode_id=$(LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli linodes list --format id --text --no-header | head -n 1)

    SECONDS=0
    until [[ $(LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]]; do
        echo 'still provisioning'
        sleep 5 # Wait 5 seconds before checking status again, to rate-limit ourselves
        if (( $SECONDS > 180 )); then
            echo "Failed to provision.. Failed after $SECONDS seconds" >&3
            assert_failure # Fail test, linode did not boot in time
            break
        fi
    done
}

waitForSsh() {
    local linode_label=$(linode-cli linodes list --format "label" --text --no-headers)
    local linode_ip=$(linode-cli linodes list --format "ipv4" --text --no-headers)

    # Wait until SSH is available
    SECONDS=0
    sshUp=$(nc -z -G 2 "$linode_ip" 22  || echo "port closed")

    while [ "$sshUp" == "port closed" ]; do
        # Timeout if it takes more than 15 seconds for ssh availability
        if (( "$SECONDS" > 15)); then
            break
        fi
        sshUp=$(nc -z -G 2 "$linode_ip" 22 || echo "port closed")
    done
}

setToken() {
    source $PWD/.env

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

    run bash -c "echo -e \"export TOKEN_1=$TOKEN_1\nexport TOKEN_2=$TOKEN_2\nexport TOKEN_1_IN_USE_BY=$TOKEN_1_IN_USE_BY\nexport TOKEN_2_IN_USE_BY=$TOKEN_2_IN_USE_BY\nexport TEST_ENVIRONMENT=$TEST_ENVIRONMENT\" > ./.env"
}

clearToken() {
    source $PWD/.env

    if [ "$TOKEN_1_IN_USE_BY" = $1 ]; then
        export TOKEN_1_IN_USE_BY=NONE
    elif [ "$TOKEN_2_IN_USE_BY" = $1 ]; then
        export TOKEN_2_IN_USE_BY=NONE
    fi

    unset LINODE_CLI_TOKEN

    run bash -c "echo -e \"export TOKEN_1=$TOKEN_1\nexport TOKEN_2=$TOKEN_2\nexport TOKEN_1_IN_USE_BY=$TOKEN_1_IN_USE_BY\nexport TOKEN_2_IN_USE_BY=$TOKEN_2_IN_USE_BY\nexport TEST_ENVIRONMENT=$TEST_ENVIRONMENT\" > ./.env"
}
