#!/usr/bin/env bats

load '../test_helper/bats-assert/load'
load '../test_helper/bats-support/load'
load '../common'

export nodebalancerCreated="[0-9]+,balancer[0-9]+,us-east,[0-9]+-[0-9]+-[0-9]+-[0-9]+.ip.linodeusercontent.com,0"

setup() {
	suiteName="nodebalancers"
	setToken "$suiteName"
}

teardown() {
    if [ "$LAST_TEST" = "TRUE" ]; then
        clearToken "$suiteName"
    fi
}

@test "it should fail to create a nodebalancer without specifying a region" {
    run linode-cli nodebalancers create \
    	--text \
    	--no-headers
    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "region	region is required"
}

@test "it should create a nodebalancer with a default configuration" {
	run linode-cli nodebalancers create \
		--region us-east \
		--text \
		--delimiter "," \
		--format="id,label,region,hostname,client_conn_throttle"

	assert_success
	assert_output --regexp $nodebalancerCreated
}

@test "it should list the available nodebalancers and output their status" {
	run linode-cli nodebalancers list \
		--text \
		--no-headers \
		--delimiter "," \
		--format="id,label,region,hostname,client_conn_throttle"

	assert_success
	assert_output --regexp $nodebalancerCreated
}

@test "it should display the public ipv4 for the nodebalancer" {
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)

	run linode-cli nodebalancers view $nodebalancerId \
		--format="ipv4" \
		--text \
		--no-headers
	assert_success
	assert_output --regexp "^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
}

@test "it should fail to view a nodebalancer with an invalid nodebalancer id" {
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)

	run linode-cli nodebalancers view 535\
		--text \
		--no-headers
	assert_failure
	assert_output --partial "Request failed: 404"
	assert_output --partial "Not found"
}

@test "it should create a standard configuration profile" {
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)

	run linode-cli nodebalancers config-create $nodebalancerId \
		--delimiter "," \
		--text \
		--no-headers

	assert_success
	assert_output --regexp "[0-9]+,80,http,roundrobin,none,True,recommended,,"
}

@test "it should view the configuration profile" {
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)
	configId=$(linode-cli nodebalancers configs-list $nodebalancerId --text --no-headers --format=id)

	run linode-cli nodebalancers config-view $nodebalancerId $configId \
		--text \
		--no-headers \
		--delimiter ","

	assert_success
	assert_output --regexp "[0-9]+,80,http,roundrobin,none,True,recommended,,"
}

@test "it should add a node to the configuration profile" {
	nodeIp=$(linode-cli linodes create \
	     --root_pass aComplex@Password \
	     --booted true \
	     --region us-east \
	     --type g6-standard-2 \
	     --private_ip true \
	     --image=$test_image \
	     --text \
	     --no-headers \
	     --format "ip_address" | egrep -o "192.168.[0-9]{1,3}.[0-9]{1,3}")
	nodeLabel="testnode1"
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)
	configId=$(linode-cli nodebalancers configs-list $nodebalancerId --text --no-headers --format=id)

	run linode-cli nodebalancers node-create \
		--address $nodeIp:80 \
		--label $nodeLabel \
		--weight "100" \
		--text \
		--no-headers \
		--delimiter "," \
		$nodebalancerId \
		$configId

	assert_success
	assert_output --regexp "[0-9]+,$nodeLabel,$nodeIp:80,Unknown,100,accept"
}

@test "it should update a node label" {
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)
	configId=$(linode-cli nodebalancers configs-list $nodebalancerId --text --no-headers --format=id)
	nodeId=$(linode-cli nodebalancers nodes-list $nodebalancerId $configId --text --no-headers --format=id)
	nodeIp=$(linode-cli nodebalancers node-view $nodebalancerId $configId $nodeId --format "address" --text --no-headers)
	newLabel="testnode1-edited"

	run linode-cli nodebalancers node-update $nodebalancerId $configId $nodeId \
		--label $newLabel \
		--text \
		--no-headers \
		--delimiter ","

	assert_success
	assert_output --regexp "[0-9]+,$newLabel,$nodeIp,Unknown,100,accept"
}

@test "it should update the node port" {
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)
	configId=$(linode-cli nodebalancers configs-list $nodebalancerId --text --no-headers --format=id)
	nodeId=$(linode-cli nodebalancers nodes-list $nodebalancerId $configId --text --no-headers --format=id)
	nodeAddress=$(linode-cli nodebalancers node-view $nodebalancerId $configId $nodeId --format "address" --text --no-headers)

	updatedPort=":23"
	updatedAddress=$(echo "${nodeAddress/:80/$updatedPort}")

	run linode-cli nodebalancers node-update $nodebalancerId $configId $nodeId \
		--address $updatedAddress \
		--text  \
		--no-headers \
		--delimiter ","

	assert_success
	assert_output --regexp "[0-9]+,testnode1-edited,$updatedAddress,Unknown,100,accept"
}

@test "it should fail to update node to a public IPv4 address" {
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)
	configId=$(linode-cli nodebalancers configs-list $nodebalancerId --text --no-headers --format=id)
	nodeId=$(linode-cli nodebalancers nodes-list $nodebalancerId $configId --text --no-headers --format=id)
	nodeIp=$(linode-cli nodebalancers node-view $nodebalancerId $configId $nodeId --format "address" --text --no-headers)
	publicIp="8.8.8.8:80" # example public ipv4

	run linode-cli nodebalancers node-update $nodebalancerId $configId $nodeId \
		--address $publicIp \
		--text \
		--no-headers

	assert_failure
	assert_output --partial "Request failed: 400"
	assert_output --partial "address	Must begin with 192.168"
}

@test "it should remove a node from a configuration profile" {
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)
	configId=$(linode-cli nodebalancers configs-list $nodebalancerId --text --no-headers --format=id)
	nodeId=$(linode-cli nodebalancers nodes-list $nodebalancerId $configId --text --no-headers --format=id)

	run linode-cli nodebalancers node-delete $nodebalancerId $configId $nodeId
	assert_success
}

@test "it should update the port of a configuration profile" {
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)
	configId=$(linode-cli nodebalancers configs-list $nodebalancerId --text --no-headers --format=id)

	run linode-cli nodebalancers config-update \
		--port 10700 \
		--protocol tcp \
		$nodebalancerId \
		$configId \
		--text \
		--no-headers \
		--delimiter ","

	assert_success
	assert_output --regexp "[0-9]+,10700,tcp,roundrobin,none,True,recommended,,"

}

@test "it should add an additional configuration profile" {
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)

	run linode-cli nodebalancers config-create $nodebalancerId \
		--delimiter "," \
		--text \
		--no-headers

	assert_success
	assert_output --regexp "[0-9]+,80,http,roundrobin,none,True,recommended,,"
}

@test "it should list multiple configuration profiles" {
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)

	run linode-cli nodebalancers configs-list $nodebalancerId \
		--delimiter "," \
		--text \
		--no-headers

	assert_success
	assert_output --regexp "[0-9]+,80,http,roundrobin,none,True,recommended,,"
	assert_output --regexp "[0-9]+,10700,tcp,roundrobin,none,True,recommended,,"
}

@test "it should remove a configuration profile" {
	nodebalancerId=$(linode-cli nodebalancers list --format=id --text --no-headers)
	configurationIds=$(linode-cli nodebalancers configs-list $nodebalancerId --text --no-headers --format=id)

	set -- $configurationIds
	configId=$1

	run linode-cli nodebalancers config-delete $nodebalancerId $configId

	assert_success
}

@test "it should delete all nodebalancers" {
	LAST_TEST="TRUE"
	run removeAll "nodebalancers"
	run removeAll "linodes"
}
