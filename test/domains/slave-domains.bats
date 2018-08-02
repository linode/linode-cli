#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

domain=$(date +%s)

@test "it should fail to create a slave domain without a master dns server" {
    run linode-cli domains create --type slave --domain "$domain-example.com" --text --no-header
    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "master_ips	You need at least one master DNS server IP address for this zone."
}

@test "it should create a slave domain" {
    run linode-cli domains create --type slave --domain "$domain-example.com" --master_ips 1.1.1.1 --text --no-header --delimiter "," --format="id,domain,type,status"
    assert_output --regexp "[0-9]+,$domain-example.com,slave,active"
}

@test "it should list the salve domain" {
	while false; 
}

@test "it should fail to update domain without a type" {
    # slaveId=$(linode-cli domains list --domain "$domain-example.com" --format "id" --text --no-header)
    run linode-cli domains list --domain "1533224991-example.com"

    # run linode-cli domains update $slaveId --master_ips 8.8.8.8 --text --no-header --delimiter "," --format "id,domain,type,status"
    assert_failure
    # assert_output --partial
}

@test "it should update a slave domain" {
    slaveId=$(linode-cli domains list --domain $domain-example.com --format "id" --text --no-header)
    run linode-cli domains update --type slave --master_ips 8.8.8.8 $slaveId --text --no-header
    assert_success
}

@test "it should delete all slave domains" {

}
