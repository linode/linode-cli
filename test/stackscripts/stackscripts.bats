#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

##################################################################
#  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
#  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
##################################################################

EXAMPLE_SCRIPT="echooo foo > test.sh"

@test "it should list stackscripts" {
    run linode-cli stackscripts list \
        --text
    assert_success
    assert_output --partial "id	username	label	images	is_public	created	updated"

    run bash -c "linode-cli stackscripts list \
    	--text \
    	--no-headers \
    	--format "id,username,is_public,created,updated" \
    	--delimiter ',' \
    	| head -n 1"

    assert_success
    assert_output --regexp "[0-9]+,[a-z]+,True,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+"
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
		--script "#!/bin/bash \n $EXAMPLE_SCRIPT" \
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
	newImage="linode/debian8"
	privateStackscript=$(linode-cli stackscripts list --is_public false --text --no-headers --format "id")
	run linode-cli stackscripts update \
		--images $newImage \
		$privateStackscript \
		--text \
		--no-headers \
		--delimiter ","

	assert_success
	assert_output --regexp "[0-9]+,.*,testfoo,$newImage,False,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+"
}

@test "it should fail to deploy a stackscript to a linode from an incompatible image" {
	privateStackscript=$(linode-cli stackscripts list --is_public false --text --no-headers --format "id")
	compatibleImage="linode/debian8"
	linodePlan="g6-standard-1"
	linodeRegion="us-east"

	run linode-cli linodes create --stackscript_id $privateStackscript \
		--type $linodePlan \
		--image "linode/arch" \
		--region $linodeRegion \
		--root_pass $random_pass \
		--text \
		--no-headers

	assert_failure
	assert_output --partial "The requested distribution is not supported by this stackscript."
	assert_output --partial "Request failed: 400"
}

@test "it should deploy a linode from a stackscript" {
	compatibleImage="linode/debian8"
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
	privateStackscript=$(linode-cli stackscripts list --is_public false --text --no-headers --format "id")
	run linode-cli stackscripts delete $privateStackscript

	assert_success

	run removeAll "linodes"
}
