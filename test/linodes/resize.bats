load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

##################################################################
#  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
#  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
##################################################################

setup() {
    export timestamp=$(date +%s)
    local plan=$(linode-cli linodes types --format="id" --text --no-headers | sed -n 2p)
    run createLinodeAndWait $plan
    linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
}

teardown() {
    unset timestamp
    run removeLinodes
}

@test "it should fail to resize to the same plan" {
    # linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
    linode_plan=$(linode-cli linodes view $linode_id --format="type" --text --no-headers)

    run linode-cli linodes resize \
        --type=$linode_plan \
        --text \
        --no-headers \
        $linode_id

    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "Linode is already running this service plan."

}

@test "it should fail to resize to a smaller plan" {
	smaller_plan=$(linode-cli linodes types --format="id" --text --no-headers | sed -n 1p)
	# linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
	run linode-cli linodes resize \
		--type=$smaller_plan \
		--text \
        --no-headers \
		$linode_id

	assert_failure
	assert_output --partial "Request failed: 400"
	assert_output --partial "Linode has allocated more disk than the new service plan allows. Delete or resize disks smaller."
}

@test "it should fail to resize to an invalid plan" {
	invalid_plan="g15-bad-plan"
	run linode-cli linodes resize \
		--type=$invalid_plan \
		--text \
        --no-headers \
		$linode_id

	assert_failure
	assert_output --partial "Request failed: 400"
	assert_output --partial "type	A valid Linode type by that ID was not found"
}

@test "it should resize the linode to the next size plan" {
	larger_plan=$(linode-cli linodes types --format="id" --text --no-headers | sed -n 3p)
	run linode-cli linodes resize \
		--type=$larger_plan \
		--text \
		--no-headers \
		$linode_id

	assert_success

	# Wait for status = "Resizing"
	until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "resizing" ]; do
        echo 'waiting for resize to start'
    done

	# Wait for offline status.
	# Linodes that are resized do not boot automatically
    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "offline" ]; do
        echo 'still resizing'

		# Check for resizing completion every 15 seconds
        sleep 15
    done

    run linode-cli linodes view $linode_id \
    	--format="type" \
    	--text \
    	--no-headers

    assert_success
    assert_output $larger_plan
}
