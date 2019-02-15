load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

##################################################################
#  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
#  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
##################################################################

setup() {
    export timestamp=$(date +%s)
    run createLinode
    linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
    SECONDS=0
}

teardown() {
    unset timestamp
    run removeLinodes
}

@test "it should create a linode and be provisioning status" {
    run linode-cli linodes view $linode_id \
        --format="status" \
        --text \
        --no-headers

    assert_success
    assert_output "provisioning"
}

@test "it should create a linode and boot" {
    # Wait For Linode to be Running
    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]; do
        echo 'still provisioning'
        sleep 5 # Rate limit ourselves
        if [[ "$SECONDS" -eq 180 ]];
        then
            echo "Timeout elapsed! Linode did not boot in time"
            assert_failure  # This will fail the test
            break
        fi
    done
}

@test "it should reboot the linode" {
    # Wait For Linode to be Running
    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]; do
        echo "still provisioning"
        sleep 5 # Rate limit ourselves
        if [[ "$SECONDS" -eq 180 ]];
        then
            echo "Timeout elapsed! Linode did not boot in time"
            assert_failure  # This will fail the test
            break
        fi
    done

    run linode-cli linodes reboot $linode_id \
        --text \
        --no-headers
    assert_success

    # Wait For Linode to NOT be running
    SECONDS=0
    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) != "running" ]; do
        sleep 5 # Rate limit ourselves
        if [[ "$SECONDS" -eq 180 ]];
        then
            echo "Timeout elapsed! Linode did not reboot in time"
            assert_failure # This will fail the test
            break
        fi
    done
}

@test "it should shutdown the linode" {
    # Wait For Linode to be Running
    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]; do
        echo 'still provisioning'
        sleep 5 # Rate limit ourselves
        if [[ "$SECONDS" -eq 180 ]];
        then
            echo "Timeout elapsed! Linode did not start running in time"
            assert_failure # This will fail the test
            break
        fi
    done

    run linode-cli linodes shutdown $linode_id
    assert_success

    # Wait For Linode to be offline
    SECONDS=0
    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "offline" ]; do
        echo 'still shutting down'
        sleep 5 # Rate limit ourselves
        if [[ "$SECONDS" -eq 180 ]];
        then
            echo "Timeout elapsed! Linode did not shutdown in time"
            assert_failure # This will fail the test
            break
        fi
    done
}

