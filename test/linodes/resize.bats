load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

##################################################################
#  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
#  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
##################################################################

setup() {
    suiteName="resize"
    setToken "$suiteName"
    export timestamp=$(date +%s)
}

teardown() {
    unset timestamp
    run removeLinodes

    if [ "$LAST_TEST" = "TRUE" ]; then
        clearToken "$suiteName"
    fi
}

@test "it should fail to resize to the same plan" {
    local plan=$(linode-cli linodes types --format="id" --text --no-headers | sed -n 2p)
    run createLinodeAndWait $plan
    linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
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
	local plan=$(linode-cli linodes types --format="id" --text --no-headers | sed -n 2p)

    run createLinodeAndWait $plan
    linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)

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
    local plan=$(linode-cli linodes types --format="id" --text --no-headers | sed -n 2p)
    run createLinodeAndWait $plan
    linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
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
    LAST_TEST="TRUE"
    if [ $RUN_LONG_TESTS = "TRUE" ]; then
    	larger_plan=$(linode-cli linodes types --format="id" --text --no-headers | sed -n 3p)
    	run linode-cli linodes resize \
    		--type=$larger_plan \
    		--text \
    		--no-headers \
    		$linode_id

    	assert_success

    	# Wait for status = "Resizing"
        SECONDS=0
    	until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "resizing" ]; do
            echo 'waiting for resize to start'
            sleep 5
            if [[ "$SECONDS" -eq 180 ]]
            then
                assert_failure # Linode failed to start resizing
                break
            fi
        done

    	# Wait for offline status.
    	# Linodes that are resized do not boot automatically
        SECONDS=0
        until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "offline" ]; do
            echo 'still resizing'

    		# Check for resizing completion every 15 seconds
            sleep 15
            if [[ "$SECONDS" -eq 600 ]];
            then
                assert_failure # Linode failed to completge resizing within 10 minutes
                break
            fi
        done

        run linode-cli linodes view $linode_id \
        	--format="type" \
        	--text \
        	--no-headers

        assert_success
        assert_output $larger_plan

    else
        skip "Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE"
    fi
}
