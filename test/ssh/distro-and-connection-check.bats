#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

# ##################################################################
# #  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
# #  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
# ##################################################################

setup() {
    suiteName="distro-and-connection-check"
    setToken "$suiteName"
}

teardown() {
    if [ "$LAST_TEST" = "TRUE" ]; then
        run removeLinodes
        clearToken "$suiteName"
    fi
}

@test "it should create a linode and wait for it to be running" {
    run removeLinodes
    alpine_image=$(linode-cli images list --format "id" --text --no-headers | grep 'alpine' | xargs | awk '{ print $1 }')
    plan=$(linode-cli linodes types --text --no-headers --format="id" | xargs | awk '{ print $1 }')
    ssh_key="$(cat ~/.ssh/id_rsa.pub)"
    createLinodeAndWait "$alpine_image" "$plan" "$ssh_key"
    assert_success
}

@test "it should confirm the distro image is the distro selected in the CLI" {
    # Replace this with polling for ssh port open
    sleep 25

    linode_label=$(linode-cli linodes list --format "label" --text --no-headers)
    run linode-cli ssh "root@$linode_label" -oStrictHostKeyChecking=no "cat /etc/os-release"
    assert_success
    assert_output --partial "Alpine Linux"
}


@test "it should check the vm for ipv4 connectivity" {
    LAST_TEST="TRUE"
    linode_label=$(linode-cli linodes list --format "label" --text --no-headers)
    run linode-cli ssh "root@$linode_label" -oStrictHostKeyChecking=no "ping -4 -W60 -c3 google.com"
    assert_success
    assert_output --partial "0% packet loss"
}
