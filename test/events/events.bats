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
        clearToken "$suiteName"
    fi
}

@test "it should print the usage information" {
    run linode-cli events
    assert_success
    assert_output --partial "linode-cli events [ACTION]"
    assert_output --regexp "list.*List Events"
    assert_output --regexp "view.*View Event"
    assert_output --regexp "mark-read.*Mark Event as Read"
    assert_output --regexp "mark-seen.*Mark Event as Seen"
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
    LAST_TEST="TRUE"
    event_id=$(linode-cli events list --format "id" --text --no-headers | xargs |  awk '{ print $1 }')
    run linode-cli events mark-read "$event_id" --text --no-headers --delimiter ","
    assert_success
    run linode-cli events view "$event_id" --text --no-headers --delimiter ","
    assert_success
    assert_output --regexp "[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,[a-z]+,(True|False),True"
}