#!/usr/bin/env bats

load '../test_helper/bats-assert/load'
load '../test_helper/bats-support/load'
load '../common'

setup() {
    suiteName="users"
    setToken "$suiteName"
}

teardown() {
    if [ "$LAST_TEST" = "TRUE" ]; then
        clearToken "$suiteName"
        rm .tmp-user
    fi
}

@test "it should display users" {
    run linode-cli users list
    assert_success
}

@test "it should create a user" {
    echo "export user=$uniqueUser" > .tmp-user
    run linode-cli users create \
        --username $uniqueUser \
        --email $uniqueUser@linode.com \
        --restricted true \
        --text \
        --no-headers
    assert_success
}

@test "it should view a user" {
    source .tmp-user

    run linode-cli users view $user
    assert_success
}

@test "it should remove a user" {
    LAST_TEST="TRUE"
    source .tmp-user

    run linode-cli users delete $user
    assert_success
}
