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

@test "it should fail to access an invalid host" {
    export LINODE_CLI_API_HOST=wrongapi.linode.com
    run linode-cli linodes ls

    assert_failure
    assert_output --partial "wrongapi.linode.com"
}

@test "it should use v4beta when override is set" {
    export LINODE_CLI_API_VERSION=v4beta
    run linode-cli linodes ls --debug

    assert_success
    assert_output --partial "v4beta"
}

@test "it should fail to access an invalid api scheme" {
    export LINODE_CLI_API_SCHEME=ssh
    run linode-cli linodes ls

    assert_failure
    assert_output --partial "ssh"
}