#!/usr/bin/env bats

load '../test_helper/bats-assert/load'
load '../test_helper/bats-support/load'
load '../common'

setup() {
    suiteName="tags"
    setToken "$suiteName"
}

teardown() {
    if [ "$LAST_TEST" = "TRUE" ]; then
        clearToken "$suiteName"
        rm .tmp-tag
    fi
}

@test "it should display tags" {
    run linode-cli tags list
    assert_success
}

@test "it should create a tag" {
    echo "export tag=$uniqueTag" > .tmp-tag
    run linode-cli tags create \
        --label $uniqueTag \
        --text \
        --no-headers
    assert_success
}

@test "it should view the unique tag" {
    source .tmp-tag

    run linode-cli tags list \
        --text \
        --no-headers

    assert_success
    assert_output --partial "$tag"
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
    LAST_TEST="TRUE"
    source .tmp-tag

    run linode-cli tags delete $tag
    assert_success
}
