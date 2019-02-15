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
}

teardown() {
    unset timestamp

    if [ "$clean_linodes" = "true" ];
    then
        run removeLinodes
    fi
}

@test "it should create a linode with backups disabled" {
    run createLinode
    local linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
    run linode-cli linodes backups-cancel $linode_id --text

    assert_failure
    assert_output --partial "Request failed: 400"
    assert_output --partial "This Linode does not have a backup service to cancel."
}

@test "it should enable backups" {
    run linode-cli linodes backups-enable $linode_id \
        --text \
        --no-headers
    assert_success

    run linode-cli linodes backups-cancel $linode_id \
        --text \
        --no-headers
    assert_success

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
    assert_success
}

@test "it should take a snapshot of a linode" {
    SECONDS=0
    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]; do
        echo 'still provisioning'
        # Wait 3 seconds before checking status again, to rate-limit ourselves
        sleep 3
        if [[ "$SECONDS" -eq 180 ]];
        then
            assert_failure # Linode failed to boot
            break
        fi
    done
    snapshot_label="test_snapshot1"
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
        --text \
        --no-headers
    assert_success
    assert_output --regexp "[0-9]+,pending,snapshot,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,${snapshot_label}"
}

# @test "it should restore the linode from a snapshot" {

# }

@test "it should cancel backups" {
    run linode-cli linodes backups-cancel $linode_id \
        --text \
        --no-headers
    assert_success

    clean_linodes="true"
}
