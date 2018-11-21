#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

setup() {
    export timestamp=$(date +%s)
}

teardown() {
    unset timestamp
}

@test "it should fail to create a master domain with invalid tags" {
    skip "BUG 943"

    badTag="*"
    timestamp=$(date +%s)
    run linode-cli domains create \
        --type master \
        --soa_email="pthiel+$timestamp@linode.com" \
        --domain "$timestamp-example.com" \
        --tags "$badTag" \
        --text \
        --no-header \
        --delimiter ","
        --format="id,domain,type,status,soa_email,tags" \
        --suppress-warnings

    assert_failure
}

@test "it should fail to create a slave domain with invalid tags" {
    skip "BUG 943"

    badTag="*2"
    run linode-cli domains create \
        --type slave \
        --soa_email="pthiel345@linode.com" \
        --domain "$timestamp-example.com" \
        --tags "$badTag" \
        --text \
        --no-header \
        --delimiter "," \
        --format="id,domain,type,status,soa_email,tags"

    assert_failure
}

@test "it should create a master domain with tags" {
    tag="foo"
    email="pthiel+$timestamp@linode.com"
    run linode-cli domains create \
        --type master \
        --soa_email="$email" \
        --domain "$timestamp-example.com" \
        --tags "$uniqueTag" \
        --format="id,domain,type,status,tags" \
        --suppress-warnings \
        --text \
        --no-header \
        --delimiter=","

    assert_success
    assert_output --regexp "[0-9]+,[0-9]+-example.com,master,active,${uniqueTag}"
}

@test "it should cleanup domains and tags" {
    run removeDomains
    run removeUniqueTag
}
