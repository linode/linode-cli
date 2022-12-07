#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

# ##################################################################
# #  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
# #  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
# ##################################################################

setup() {
    suiteName="ssh"
    setToken "$suiteName"
}

teardown() {
    if [ "$LAST_TEST" = "TRUE" ]; then
        run removeLinodes
        clearToken "$suiteName"
    fi
}

@test "it should display the ssh plugin usage information" {
    run removeLinodes
    run linode-cli ssh -h

    assert_success
    assert_output --partial "usage: linode-cli ssh [-h] [-6] [[USERNAME@]LABEL]"
    assert_output --partial "positional arguments:"
    assert_output --partial "[USERNAME@]LABEL  The label of the Linode to SSH into, optionally with a"
    assert_output --partial "username before it in USERNAME@LABEL format. If no"
    assert_output --partial "username is given, defaults to the current user."
    assert_output --partial "option"
    assert_output --partial "-h, --help        show this help message and exit"
    assert_output --partial "-6                If given, uses the Linode's SLAAC address for SSH."
}

@test "it should create a linode and wait for it to be running" {
    alpine_image=$(linode-cli images list --format "id" --text --no-headers | grep 'alpine' | xargs | awk '{ print $1 }')
	plan=$(linode-cli linodes types --text --no-headers --format="id" | xargs | awk '{ print $1 }')

	ssh_key="$(cat $random_key_public)"

	createLinodeAndWait "$alpine_image" "$plan" "$ssh_key"
	assert_success
}

@test "it should fail to ssh into a linode that does not match any existing linodes" {
	run linode-cli ssh root@aasdkjlf
	assert_failure
	assert_output "No Linode found for label aasdkjlf"
}

@test "it should successfully ssh into a linode and get the kernel version" {
    LAST_TEST="TRUE"
    ## Figure out a better way to get IP of a linode label
    linode_label=$(linode-cli linodes list --format "label" --text --no-headers)
    linode_ip=$(linode-cli linodes list --format "ipv4" --text --no-headers)

    # Poll until SSH is available
    SECONDS=0
    until nc -z $linode_ip 22
    do
        sleep 1

        if (( $SECONDS > 240 )); then
            echo "Timeout elapsed! Could not connect to SSH in time"
            assert_failure  # This will fail the test
        fi
    done

	run linode-cli ssh "root@$linode_label" -i "${random_key_private}" -oStrictHostKeyChecking=no uname -r
	assert_success
	# Assert the kernel version matching this regex:
	assert_output --regexp "[0-9]\.[0-9]*\.[0-9]*-.*-virt"
}
