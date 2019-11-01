#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

##################################################################
#  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
#  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
##################################################################

setup() {
    suiteName="rebuild"
    setToken "$suiteName"
    export timestamp=$(date +%s)
}

teardown() {
    unset timestamp

    if [ "$LAST_TEST" = "TRUE" ]; then
        run removeLinodes
        clearToken "$suiteName"
    fi
}

@test "it should fail to rebuild without providing the image" {
    run createLinodeAndWait
    linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)

    run linode-cli linodes rebuild \
        --root_pass=$random_pass \
        $linode_id \
        --text \
        --no-headers

    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "You must specify an image"
}

@test "it should fail to rebuild with an invalid image" {
    linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
    rebuild_image="bad/image"

    run linode-cli linodes rebuild \
        --image=$rebuild_image \
        --root_pass=$random_pass \
        $linode_id \
        --text \
        --no-headers

    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "image	image is not valid"
}

@test "it should rebuild the linode" {
    LAST_TEST="TRUE"

    if [ $RUN_LONG_TESTS = "TRUE" ]; then
        linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
        rebuild_image=$(linode-cli images list --text --no-headers --format id | sed -n 3p)

        run linode-cli linodes rebuild \
            --image=$rebuild_image \
            --root_pass=$random_pass \
            --text \
            --no-headers \
            $linode_id

        assert_success

        # Wait until rebuilding
        SECONDS=0
        until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "rebuilding" ]; do
            echo 'still running'
            sleep 5 # Wait 5 seconds between requests
            if (( $SECONDS > 180 )); then
                assert_failure # Fail if status is not rebuilding
                break
            fi
        done


        # Wait until done rebuilding
        SECONDS=0
    	until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]; do
            echo 'still rebuilding'
            sleep 5 # Wait 5 seconds between requests
            if (( $SECONDS > 180 ));
            then
                assert_failure # Linode failed to start
                break
            fi
        done

        run linode-cli linodes view $linode_id \
        	--format="image" \
        	--text \
        	--no-headers

        assert_success
        assert_output "$rebuild_image"

    else
        skip "Skipping long test, run with RUN_LONG_TESTS=TRUE to run"
    fi
}
