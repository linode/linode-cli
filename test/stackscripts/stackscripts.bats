#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

##################################################################
#  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
#  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
##################################################################

EXAMPLE_SCRIPT="echo foo > test.sh"

setup() {
	suiteName="stackscripts"
	images=$(LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli images list --format id --text --no-headers | egrep "linode\/.*")
	setToken "$suiteName"
}

teardown() {
    if [ "$LAST_TEST" = "TRUE" ]; then
    	removeAll "stackscripts"
        clearToken "$suiteName"
    fi
}

@test "it should list stackscripts" {
    run linode-cli stackscripts list \
        --text
    assert_success
    assert_output --partial "id	username	label	images	is_public	created	updated"

    run bash -c "LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli stackscripts list \
    	--text \
    	--no-headers \
    	--format "id,username,is_public" \
    	--delimiter ',' \
    	| head -n 1"

    assert_success
    assert_output --regexp "[0-9]+,([A-z]|[0-9])+,True"
}

@test "it should fail to create a stackscript without specifying an image" {
	run linode-cli stackscripts create \
		--script "$(cat ./test/stackscripts/example.sh)" \
		--label 'testfoo' \
		--is_public=false \
		--text \
		--no-headers

	assert_failure
	assert_output --partial "Request failed: 400"
	assert_output --partial "images	images is required"
}

@test "it should create a stackscript" {
	run linode-cli stackscripts create \
		--script '#!/bin/bash \n $EXAMPLE_SCRIPT' \
		--images "linode/debian9" \
		--label 'testfoo' \
		--is_public=false \
		--text \
		--no-headers \
		--delimiter ","

	assert_success
	assert_output --regexp "[0-9]+,.*,testfoo,linode/debian9,False,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+"
}

@test "it should view the private stackscript" {
	run linode-cli stackscripts list \
		--is_public false \
		--text \
		--no-headers \
		--delimiter ","

	assert_success
	assert_output --regexp "[0-9]+,.*,testfoo,linode/debian9,False,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+"
}

@test "it should update a stackscript compatible image" {
	set -- $images

	privateStackscript=$(linode-cli stackscripts list --is_public false --text --no-headers --format "id")

	run linode-cli stackscripts update \
		--images $1 \
		$privateStackscript \
		--text \
		--no-headers \
		--delimiter ","

	assert_success
	assert_output --regexp "[0-9]+,.*,testfoo,$1,False,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+"
}


@test "it should update a stackscript to be compatible with multiple images" {
	set -- $images

	privateStackscript=$(linode-cli stackscripts list --is_public false --text --no-headers --format "id")

	run linode-cli stackscripts update \
		--images $1 \
		--images $2 \
		$privateStackscript \
		--text \
		--no-headers \
		--delimiter "," \
		--format "images"

	assert_success
	assert_output --partial $1
	assert_output --partial $2
}

@test "it should fail to deploy a stackscript to a linode from an incompatible image" {
	set -- $images

	privateStackscript=$(linode-cli stackscripts list --is_public false --text --no-headers --format "id")
	linodePlan="g6-standard-1"
	linodeRegion="us-east"

	run linode-cli linodes create --stackscript_id $privateStackscript \
		--type $linodePlan \
		--image $3 \
		--region $linodeRegion \
		--root_pass $random_pass \
		--text \
		--no-headers

	assert_failure
	assert_output --partial "The requested distribution is not supported by this stackscript."
	assert_output --partial "Request failed: 400"
}

@test "it should deploy a linode from a stackscript" {
	set -- $images
	compatibleImage=$1
	linodePlan="g6-standard-1"
	linodeRegion="us-east"
	privateStackscript=$(linode-cli stackscripts list --is_public false --text --no-headers --format "id")

	run linode-cli linodes create \
		--stackscript_id $privateStackscript \
		--type $linodePlan \
		--image $compatibleImage \
		--region $linodeRegion \
		--root_pass $random_pass \
		--text \
		--delimiter "," \
		--format "id,region,type,image" \
		--no-headers

	assert_success
	assert_output --regexp "[0-9]+,$linodeRegion,$linodePlan,$compatibleImage"
}

@test "it should delete the stackscript and teardown the linode" {
	LAST_TEST="TRUE"
	privateStackscript=$(linode-cli stackscripts list --is_public false --text --no-headers --format "id")
	run linode-cli stackscripts delete $privateStackscript

	assert_success

	run removeAll "linodes"
}
