#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

@test "it should fail to create a domain without specifying a type" {
	timestamp=$(date +%s)
	run linode-cli domains create --domain "$timestamp-example.com" --soa_email="pthiel+$timestamp@linode.com" --text --no-header
	assert_failure
	assert_output --partial "Request failed: 400"
	assert_output --partial "type	type is not valid"
}

@test "it should fail to create a master domain without a SOA email" {
	timestamp=$(date +%s)
	run linode-cli domains create --type master --domain "$timestamp-example.com" --text --no-header
	assert_failure
	assert_output --partial "Request failed: 400"
	assert_output --partial "soa_email	SOA_Email required when type=master"
}

@test "it should create a master domain" {
	timestamp=$(date +%s)
	run linode-cli domains create --type master --soa_email="pthiel+$timestamp@linode.com" --domain "$timestamp-example.com" --text --no-header --delimiter "," --format="id,domain,type,status,soa_email"
	assert_success
	assert_output --regexp "[0-9]+,$timestamp-example.com,master,active,pthiel\+$timestamp@linode.com"
}

@test "it should update the master domain" {
	
}

@test "it should list domains" {

}

@test "it should show domain detail" {

}

@test "it should delete all slave domains" {
    run removeDomains
}