#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

##################################################################
#  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
#  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
##################################################################

setup() {
    suiteName="resize-volumes"
    setToken "$suiteName"
}

teardown() {
    if [ "$LAST_TEST" = "TRUE" ]; then
        clearToken "$suiteName"
    fi
}

@test "remove all volumes prior to running tests" {
    run removeVolumes
}

@test "it should fail to resize a volume smaller" {
    createVolume
    volume_id=$(linode-cli volumes list --text --no-headers --format="id" | tail -n1)
    #  we can't resize a busy volume; wait for a few seconds for the creation to finish
    sleep 5
    run linode-cli volumes resize $volume_id \
        --size=5 \
        --text \
        --no-headers

    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "Storage volumes can only be resized up"
}

@test "it should fail to resize a volume greater than 10240gb" {
    volume_id=$(linode-cli volumes list --text --no-headers --format="id" | tail -n1)
    run linode-cli volumes resize $volume_id \
        --size=1024893405 \
        --text \
        --no-headers

    assert_failure
    assert_output --partial "Request failed: 400"

    if [ "$TEST_ENVIRONMENT" = "dev" ] || [ "$TEST_ENVIRONMENT" = "test" ]; then
        assert_output --partial "Storage volumes cannot be resized larger than 1024 gigabytes"
    else
        assert_output --partial "Storage volumes cannot be resized larger than 10240 gigabytes"
    fi
}

@test "it should resize a volume" {
    volume_id=$(linode-cli volumes list --text --no-headers --format="id" | tail -n1)
    run linode-cli volumes resize $volume_id \
        --size=11 \
        --text \
        --no-headers

    assert_success

    run linode-cli volumes view $volume_id \
        --format="size" \
        --text \
        --no-headers

    assert_success
    assert_output "11"
}

@test "it should remove all volumes" {
    LAST_TEST="TRUE"
    run removeVolumes
}
