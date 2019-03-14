#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

##################################################################
#  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
#  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
##################################################################

setup() {
    suiteName="list-view-update-volumes"
    setToken "$suiteName"
    export volume_id=$(linode-cli volumes list --text --no-headers --delimiter="," --format="id" )
}

teardown() {
    unset volume_id
}

@test "it should list volumes" {
    run createVolume
    run linode-cli volumes list \
        --text \
        --no-headers \
        --delimiter=","

    assert_success
    assert_output --regexp "[0-9]+,A[0-9]+,(creating|active),10,us-east"
}

@test "it should view a single volume" {
    run linode-cli volumes view $volume_id \
        --text \
        --no-headers \
        --delimiter="," \
        --format="id,label,size,region"

    assert_success
    assert_output --regexp "$volume_id,A[0-9]+,10,us-east"
}

@test "it should update a volume label" {
    run linode-cli volumes update \
        --label=A-NewLabel-2 $volume_id \
        --text \
        --no-headers \
        --format="label"

    assert_success
    assert_output "A-NewLabel-2"
}

@test "it should add a new tag to a volume" {
    run linode-cli volumes update $volume_id \
        --tags=$uniqueTag \
        --format="tags" \
        --text \
        --no-headers

    assert_success
    assert_output "$uniqueTag"
}

@test "it should view tags attached to the volume" {
    run linode-cli volumes view $volume_id \
        --tags "" \
        --format="tags" \
        --text \
        --no-headers

    assert_output "$uniqueTag"
    assert_success
}

@test "it should fail to update volume size" {
    run linode-cli volumes update \
        --size=15 $volume_id \
        --text \
        --no-headers \
        --format="size"

    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "size	size is not an editable field"
}

@test "it should remove all volumes and unique tags" {
    run removeVolumes
    run removeUniqueTag
    clearToken "$suiteName"
}
