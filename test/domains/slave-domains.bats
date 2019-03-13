#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

domainTimeStamp=0

setup() {
    export suiteName="slave-domains"
}

@test "it should fail to create a slave domain without a master dns server" {
    setToken "$suiteName"

    domainTimeStamp="$(date +"%s")"
    run linode-cli domains create --type slave --domain "$domainTimeStamp-example.com" --text --no-header
    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "master_ips	You need at least one master DNS server IP address for this zone."
}

@test "it should create a slave domain" {
    getToken "$suiteName"

    run linode-cli domains create --type slave --domain "$domainTimeStamp-example.com" --master_ips 1.1.1.1 --text --no-header --delimiter "," --format="id,domain,type,status"
    assert_output --regexp "[0-9]+,$domainTimeStamp-example.com,slave,active"
}

@test "it should list the slave domain" {
    getToken "$suiteName"

    run linode-cli domains list --text --no-header
    assert_output --partial "$domainTimeStamp-example.com"
}

@test "it should fail to update domain without a type" {
    skip "BUG 872"
    slaveId=$(linode-cli domains list --domain "$domainTimeStamp-example.com" --format "id" --text --no-header)
    run linode-cli domains update $slaveId --master_ips 8.8.8.8 --text --no-header --deleteimiter "," --format "id,domain,type,status"
    assert_failure
    # assert_output --partial
}

@test "it should update a slave domain" {
    getToken "$suiteName"

    slaveId=$(linode-cli domains list --domain $domainTimeStamp-example.com --format "id" --text --no-header)
    run linode-cli domains update --type slave --master_ips 8.8.8.8 $slaveId --text --no-header
    assert_success
}

@test "it should delete all slave domains" {
    getToken "$suiteName"
    run removeDomains
    clearToken "$suiteName"
}
