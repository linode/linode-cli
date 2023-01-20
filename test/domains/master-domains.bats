#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

setup() {
	export timestamp=$(date +%s)
	suiteName="master-domains"
	setToken $suiteName
}

teardown() {
	unset timestamp

	if [ "$LAST_TEST" = "TRUE" ]; then
        clearToken "$suiteName"
    fi
}

@test "it should fail to create a domain without specifying a type" {
	run linode-cli domains create \
		--domain "BC$timestamp-example.com" \
		--soa_email="pthiel+$timestamp@linode.com" \
		--text \
		--no-header

	assert_failure
	assert_output --partial "Request failed: 400"
	assert_output --partial "type	type is required"
}

@test "it should fail to create a master domain without a SOA email" {
	run linode-cli domains create \
		--type master \
		--domain "BC$timestamp-example.com" \
		--text \
		--no-header

	assert_failure
	assert_output --partial "Request failed: 400"
	assert_output --partial "soa_email	soa_email required when type=master"
}

@test "it should create a master domain" {
	run linode-cli domains create \
		--type master \
		--soa_email="pthiel+$timestamp@linode.com" \
		--domain "BC$timestamp-example.com" \
		--text \
		--no-header \
		--delimiter "," \
		--format="id,domain,type,status,soa_email"

	assert_success
	assert_output --regexp "[0-9]+,BC$timestamp-example.com,master,active,pthiel\+$timestamp@linode.com"
}

@test "it should update the master domain soa_email" {
	# Remove --master_ips param when 872 is resolved
	newSoaEmail='pthiel@linode.com'

	run linode-cli domains update $(linode-cli domains list --text --no-header --format="id") \
		--type master \
		--master_ips 8.8.8.8 \
		--soa_email $newSoaEmail \
		--format="soa_email" \
		--text \
		--no-header

	assert_success
	assert_output --partial $newSoaEmail
}

@test "it should list master domains" {
	run linode-cli domains list \
		--format="id,domain,type,status" \
		--text \
		--no-header \
		--delimiter=","

	assert_success
	assert_output --regexp "[0-9]+,BC[0-9]+-example.com,master,active"
}

@test "it should show domain detail" {
	run linode-cli domains view $(linode-cli domains list --text --no-header --format="id") \
		--text \
		--no-header \
		--delimiter="," \
		--format="id,domain,type,status,soa_email"

	assert_success
	assert_output --regexp "[0-9]+,BC[0-9]+-example.com,master,active"
}

@test "it should delete all master domains" {
	LAST_TEST="TRUE"
    run removeDomains
}
