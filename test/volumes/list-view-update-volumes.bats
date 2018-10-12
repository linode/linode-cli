#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

##################################################################
#  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
#  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
##################################################################

@test "it should list volumes" {
    run createVolume
    run linode-cli volumes list --text --no-headers --delimiter=","
    assert_success
    assert_output --regexp "[0-9]+,A[0-9]+,(creating|active),10,us-east"
}

@test "it should view a single volume" {
    volume_id=$(linode-cli volumes list --text --no-headers --delimiter="," --format="id")
    run linode-cli volumes view $volume_id --text --no-headers --delimiter="," --format="id,label,size,region"
    assert_success
    assert_output --regexp "$volume_id,A[0-9]+,10,us-east"
}

@test "it should update a volume label" {
    volume_id=$(linode-cli volumes list --text --no-headers --delimiter="," --format="id")
    run linode-cli volumes update --label=A-NewLabel-2 $volume_id --text --no-headers --format="label"
    assert_success
    assert_output "A-NewLabel-2"
}

@test "it should fail to update volume size" {
    volume_id=$(linode-cli volumes list --text --no-headers --delimiter="," --format="id")
    run linode-cli volumes update --size=15 $volume_id --text --no-headers --format="size"
    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "size	size is not an editable field"
}

@test "it should remove all volumes" {
    run removeVolumes
}
