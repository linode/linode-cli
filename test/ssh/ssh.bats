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
    clean_linodes="false"
    # linode_label="sshTestLinode"
}

teardown() {
    if [ "$clean_linodes" = "true" ] || [ "$LAST_TEST" = "TRUE" ]; then
        run removeLinodes
    fi

    if [ "$LAST_TEST" = "TRUE" ]; then
        clearToken "$suiteName"
    fi
}

@test "it should display the ssh plugin usage infomraiton" {
    run linode-cli ssh -h

    assert_success
    assert_output --partial "usage: linode-cli ssh [-h] [-6] [[USERNAME@]LABEL]"
    assert_output --partial "positional arguments:"
    assert_output --partial "[USERNAME@]LABEL  The label of the Linode to SSH into, optionally with a"
    assert_output --partial "username before it in USERNAME@LABEL format. If no"
    assert_output --partial "username is given, defaults to the current user."
    assert_output --partial "optional arguments:"
    assert_output --partial "-h, --help        show this help message and exit"
    assert_output --partial "-6                If given, uses the Linode's SLAAC address for SSH."
}

@test "it should create a linode and wait for it to be running" {
	plan=$(linode-cli linodes types --text --no-headers --format="id" | xargs | awk '{ print $1 }')
	ssh_key="$(cat ~/.ssh/id_rsa.pub)"
	createLinodeAndWait "$plan" "$ssh_key"
	assert_success
}

@test "it should fail to ssh into a linode that does not match any existing linodes" {
	run linode-cli ssh root@aasdkjlf
	assert_failure
	assert_output "No Linode found for label aasdkjlf"
}

@test "it should successfully ssh into a linode" {
    ## Figure out a better way to get IP of a linode label
    linode_label=$(linode-cli linodes list --format "label" --text --no-headers)
	linode_ip=$(linode-cli linodes list --format "ipv4" --text --no-headers)

    # Replace this with polling for ssh port open
    sleep 25

	run linode-cli ssh "root@$linode_label" -oStrictHostKeyChecking=no uname -r
	assert_success
	# Assert the kernel version comes back:
    # Purposefully fai:
	assert_output --partial "1.19.34-0-virt"
}

@test "it should check the linode OS" {
    linode_label=$(linode-cli linodes list --format "label" --text --no-headers)
	run linode-cli ssh "root@$linode_label" -oStrictHostKeyChecking=no "cat /etc/os-release | grep -o 'NAME=.*'"
	assert_success
    assert_output --partial "Alpine Linux"
}


@test "it should check the ipv4 connectivity" {
    LAST_TEST="TRUE"
    linode_label=$(linode-cli linodes list --format "label" --text --no-headers)
    run linode-cli ssh "root@$linode_label" -oStrictHostKeyChecking=no "ping -4 -W60 -c3 google.com || ping -W60 -c3 google.com"
    assert_success
    assert_output --partial "0% packet loss"
}
