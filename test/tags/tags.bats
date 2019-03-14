#!/usr/bin/env bats

load '../test_helper/bats-assert/load'
load '../common'

setup() {
    suiteName="tags"
    setToken "$suiteName"
}

@test "it should display tags" {
    run linode-cli tags list
    assert_success
}

@test "it should create a tag" {
    run linode-cli tags create \
        --label $uniqueTag \
        --text \
        --no-headers
    assert_success
}

@test "it should view the unique tag" {
    run linode-cli tags list \
        --text \
        --no-headers

    assert_success
    assert_output --partial "$uniqueTag"
}

@test "it should fail to create a tag shorter than 3 characters" {
    run linode-cli tags create \
        --label "ba" \
        --text \
        --no-headers

    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "label	Length must be 3-50 characters"
}

@test "it should remove a tag" {
    run linode-cli tags delete $uniqueTag
    assert_success

    clearToken "$suiteName"
}
