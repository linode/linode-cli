#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

# ##################################################################
# #  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
# #  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
# ##################################################################

setup() {
    suiteName="help"
    setToken "$suiteName"
    export timestamp=$(date +%s)
    clean_linodes="FALSE"
}

@test "it should display a help page for non-aliased actions" {
    run linode-cli linodes list --help

    assert_success
    assert_output --partial "Linodes List"
    assert_output --partial "API Documentation: https://www.linode.com/docs/api/linode-instances/#linodes-list"
    assert_output --partial "You may filter results with:"
    assert_output --partial "--tags"
}

@test "it should display a help page for aliased actions" {
    run linode-cli linodes ls --help

    assert_success
    assert_output --partial "Linodes List"
    assert_output --partial "API Documentation: https://www.linode.com/docs/api/linode-instances/#linodes-list"
    assert_output --partial "You may filter results with:"
    assert_output --partial "--tags"
}

