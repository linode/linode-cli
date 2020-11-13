#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

setup() {
    suiteName="events"
    setToken "$suiteName"
}

teardown() {
    if [ "$LAST_TEST" = "TRUE" ]; then
        removeDomains
        clearToken "$suiteName"
    fi
}

@test "it should print the usage information" {
    run linode-cli events
    assert_success
    assert_output --partial "linode-cli events [ACTION]"
    assert_output --regexp "mark-read.*Event Mark as Read"
    assert_output --regexp "mark-seen.*Event Mark as Seen"
    assert_output --regexp "list.*Events List"
    assert_output --regexp "view.*Event View"
}

@test "it should list events" {
    run linode-cli events list --text --no-headers --delimiter ","
    assert_success
    assert_output --regexp "[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,[a-z]+,(True|False),(True|False)"
}

@test "it should view an event" {
    event_id=$(linode-cli events list --format "id" --text --no-headers | xargs |  awk '{ print $1 }')
    run linode-cli events view "$event_id" --text --no-headers --delimiter ","
    assert_success
    assert_output --regexp "[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,[a-z]+,(True|False),(True|False)"
}

@test "it should mark an event as seen" {
    event_id=$(linode-cli events list --format "id" --text --no-headers | xargs |  awk '{ print $1 }')
    run linode-cli events mark-seen "$event_id" --text --no-headers --delimiter ","
    assert_success
    run linode-cli events view "$event_id" --text --no-headers --delimiter ","
    assert_success
    assert_output --regexp "[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,[a-z]+,True,(True|False)"
}

@test "it should mark an event as read" {
    event_id=$(linode-cli events list --format "id" --text --no-headers | xargs |  awk '{ print $1 }')
    run linode-cli events mark-read "$event_id" --text --no-headers --delimiter ","
    assert_success
    run linode-cli events view "$event_id" --text --no-headers --delimiter ","
    assert_success
    assert_output --regexp "[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,[a-z]+,(True|False),True"
}

@test "it should filter events by entity id" {
    event_id=$(linode-cli events list --format "id" --text --no-headers | xargs |  awk '{ print $1 }')
    run linode-cli events list --id "$event_id" --text --no-headers --delimiter ","
    assert_success
    assert_output --regexp "$event_id,.*,.*,[0-9]+-[0-9][0-9]-.*,[a-z]+,(True|False),True"
}

@test "it should create a domain and filter for the domain events" {
    LAST_TEST="TRUE"
    createDomain
    domainId=$(linode-cli domains list --format="id" --text --no-headers)
    run linode-cli events list --entity.id "$domainId" --entity.type "domain" --text --no-headers --delimiter ","
    assert_success
    assert_output --regexp "[0-9]+,.*,domain_create,[0-9]+-[0-9][0-9]-.*,[a-z]+,(True|False),(True|False)"
}