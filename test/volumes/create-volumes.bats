#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

##################################################################
#  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
#  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
##################################################################

@test "it should fail to create a volume under 10gb" {
    timestamp=$(date +%s)
    run linode-cli volumes create --label "A$timestmap" --region us-east --size 5 --text --no-headers
    assert_failure
    assert_output --partial "size	Must be 10-10240"
}

@test "it should fail to create a volume without a region" {
	run linode-cli volumes create --label "A$timestamp" --size 10 --text --no-headers
    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "Must provide a region or a Linode ID"
}

@test "it should fail to create a volume without a label" {
	run linode-cli volumes create --size 10 --region us-east --text --no-headers
    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "label	label is required"
}

@test "it should fail to create a volume over 10240gb in size" {
	run linode-cli volumes create --size 10241 --label "A$timestamp" --region us-east --text --no-headers
    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "size	Must be 10-10240"
}

@test "it should fail to create a volume with an all numeric label" {
	run linode-cli volumes create --label "9200900" --region us-east --size 10 --text --no-headers
    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "label	Must begin with a letter"
}

@test "it should create an unattached volume" {
	timestamp=$(date +%s)
	run linode-cli volumes create --label "A$timestamp" --region us-east --size 10 --text --no-headers --delimiter ","
	assert_success
	assert_output --regexp "[0-9]+,A[0-9]+,creating,10,us-east"
}

# @test "it should create volume attached to a linode" {
# 	timestamp=$(date +%s)
# 	linode_id=$(linode-cli linodes list --text --no-headers --format "id")
# 	run linode-cli volumes create --label "A$timestamp" --region us-east --size 10 --linode_id=$linode_id --text --no-headers --delimiter ","
# 	assert_success
# 	assert_output --regexp "[0-9]+,A$timestamp,creating,10,us-east,$linode_id"
# }

@test "it should remove all volumes" {
	run removeLinodes
	run removeVolumes
}
