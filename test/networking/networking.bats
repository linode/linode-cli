#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

setup() {
    suiteName="networking"
    setToken "$suiteName"
    linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
}

teardown() {
    if [ "$LAST_TEST" = "TRUE" ]; then
        clearToken "$suiteName"
    fi
}

@test "it should not list any ips available on an account without linodes" {
    run linode-cli networking ips-list \
        --text \
        --no-headers
    assert_success
    assert_output ""
}


@test "it should display ips for available linodes" {
    run createLinode
    run linode-cli networking ips-list \
        --delimiter="," \
        --text \
        --no-headers

    assert_success

    assert_line --index 0 --regexp "^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
    assert_line --index 0 --regexp "ipv4,True,li[0-9].*-[0-9].*\.members.linode.com,.*,[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]"
    assert_line --index 1 --regexp "ipv6,True,,.*,[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]"

    # Gnarly Ipv6 Regex
    assert_line --index 1 --regexp "(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"
}

@test "it should view an ip address" {
    linode_ipv4=$(linode-cli linodes view $linode_id --format="ipv4" --text --no-headers)

    run linode-cli networking ip-view \
        --region="us-east" \
        --text \
        --no-headers \
        --delimiter="," \
        $linode_ipv4

    assert_success
    assert_output --regexp "^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
}

@test "it should fail to allocate an additional public ipv4 address" {
    run linode-cli networking ip-add \
        --type=ipv4 \
        --linode_id=$linode_id \
        --public=true \
        --text \
        --no-headers

    assert_failure
    assert_output --partial "Additional IPv4 addresses require technical justification.  Please open a Support Ticket describing your requirement"
}

@test "it should allocate an additional private ipv4 address" {
    LAST_TEST="TRUE"
    run linode-cli networking ip-add \
        --type=ipv4 \
        --linode_id=$linode_id \
        --delimiter="," \
        --public=false \
        --text \
        --no-headers
    assert_success
    assert_output --regexp "^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
    assert_output --regexp "ipv4,False,.*,[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]"

    run removeLinodes
}
