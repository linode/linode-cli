load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

##################################################################
#  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
#  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
##################################################################

setup() {
    run removeLinodes
    export timestamp=$(date +%s)
}

teardown() {
    unset timestamp
    run removeLinodes
}

@test "it should create a linode and be provisioning status" {
    run createLinode
    local linode_id=$(linode-cli linodes list --format="id" --text --no-headers)
    run linode-cli linodes view $linode_id \
        --format="status" \
        --text \
        --no-headers

    assert_success
    assert_output "provisioning"
}

@test "it should create a linode and boot" {
    run createLinode
    local linode_id=$(linode-cli linodes list --format="id" --text --no-headers)

    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]; do
        echo 'still provisioning'
    done

    run linode-cli linodes view $linode_id \
        --format="status" \
        --text \
        --no-headers

    assert_success
    assert_output "running"
}

@test "it should reboot the linode" {
    run createLinode
    local linode_id=$(linode-cli linodes list --format="id" --text --no-headers)

    run linode-cli linodes reboot $linode_id \
        --text \
        --no-headers

    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "booting" ]; do
        echo 'still running'
    done

    run linode-cli linodes view $linode_id \
        --format="status" \
        --text \
        --no-headers

    assert_success
    assert_output "booting"

    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]; do
        echo 'still rebooting'
    done

    run linode-cli linodes view $linode_id \
        --format="status" \
        --text \
        --no-headers

    assert_success
    assert_output "running"
}

@test "it should shutdown the linode" {
    run createLinode
    local linode_id=$(linode-cli linodes list --format="id" --text --no-headers)

    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]; do
        echo 'still provisioning'
    done

    run linode-cli linodes shutdown $linode_id
    assert_success

    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "offline" ]; do
        echo 'still shutting down'
    done

    run linode-cli linodes view $linode_id --format="status" --text --no-headers

    assert_success
    assert_output "offline"
}

