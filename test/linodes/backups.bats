load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

# ##################################################################
# #  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
# #  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
# ##################################################################

setup() {
    export timestamp=$(date +%s)
    clean_linodes="false"
    linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
    snapshot_label="test_snapshot1"
}

teardown() {
    unset timestamp

    if [ "$clean_linodes" = "true" ] || [ "$last_test" = "true" ];
    then
        run removeLinodes
    fi
}

@test "it should create a linode with backups disabled" {
    run createLinode
    local linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
    run linode-cli linodes list --format="id,enabled" \
        --delimiter="," \
        --text \
        --no-headers

    assert_success
    assert_output --partial "$linode_id,False"
}

@test "it should enable backups" {
    run linode-cli linodes backups-enable $linode_id \
        --text \
        --no-headers
    assert_success

    run linode-cli linodes list --format="id,enabled" \
        --delimiter="," \
        --text \
        --no-headers

    assert_success
    assert_output --partial "$linode_id,True"

    # Cleanup linodes
    clean_linodes="true"
}

@test "it should create a backup with backups enabled" {
    linode_type=$(linode-cli linodes types --text --no-headers --format="id" | xargs | awk '{ print $1 }')
    run linode-cli linodes create \
        --backups_enabled="true" \
        --type=$linode_type \
        --region us-east \
        --image=$test_image \
        --root_pass=$random_pass \
        --text \
        --no-headers

    linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)

    run linode-cli linodes list --format="id,enabled" \
        --delimiter="," \
        --text \
        --no-headers

    assert_success
    assert_output --partial "$linode_id,True"
}

@test "it should take a snapshot of a linode" {
    SECONDS=0
    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]; do
        echo 'still provisioning'
        # Wait 5 seconds before checking status again, to rate-limit ourselves
        sleep 5
        if [[ "$SECONDS" -eq 180 ]];
        then
            assert_failure # Linode failed to boot
            break
        fi
    done

    run linode-cli linodes snapshot $linode_id \
        --label=$snapshot_label \
        --text \
        --delimiter="," \
        --no-headers

    assert_success
    assert_output --regexp "[0-9]+,pending,snapshot,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,${snapshot_label}"
}

@test "it should view the snapshot" {
    run linode-cli linodes backups-list $linode_id \
        --delimiter="," \
        --text \
        --no-headers
    assert_success

    # assert_output --regexp "[0-9]+,pending,snapshot,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,${snapshot_label}"
    # BUG outputs the backup as json, assertion below asserts that outputs the expected.
    # assert_output --regexp ",{'updated': '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]', 'created': '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]', 'id': [0-9]*, 'label': '$snapshot_label', 'status': 'pending', 'finished': None, 'type': 'snapshot', 'region': 'us-east', 'disks': \[\], 'configs': \[\]},"
    assert_output --regexp "\'status\': \'pending."
    assert_output --regexp "\'finished\': None"
    assert_output --regexp "\'type\': \'snapshot\'"
    assert_output --regexp "\'label\': \'$snapshot_label\'"
    assert_output --regexp "\'region\': \'us-east\'"
    assert_output --regexp "\'id\': [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]"
}

# @test "it should restore the linode from a snapshot" {

# }

@test "it should cancel backups" {
    # Ensure we clean up after, even if the assertion fails
    last_test="true"

    run linode-cli linodes backups-cancel $linode_id \
        --text \
        --no-headers
    assert_success

    clean_linodes="true"
}
