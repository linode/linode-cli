#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

# ##################################################################
# #  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
# #  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
# ##################################################################

setup() {
    suiteName="backups"
    setToken "$suiteName"
    export timestamp=$(date +%s)
    clean_linodes="FALSE"
    linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)
    snapshot_label="test_snapshot1"
}

teardown() {
    unset timestamp

    if [ "$clean_linodes" = "TRUE" ] || [ "$LAST_TEST" = "TRUE" ]; then
        run removeLinodes
    fi

    if [ "$LAST_TEST" = "TRUE" ]; then
        clearToken "$suiteName"
    fi
}

@test "it should create a linode with backups disabled" {
    if [ "$TEST_ENVIRONMENT" = "dev" ] || [ "$TEST_ENVIRONMENT" = "test" ]; then
        skip "Skipping backups tests"
    fi

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
    if [ "$TEST_ENVIRONMENT" = "dev" ] || [ "$TEST_ENVIRONMENT" = "test" ]; then
        skip "Skipping backups tests"
    fi

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
    clean_linodes="TRUE"
}

@test "it should create a backup with backups enabled" {
    linode_type=$(linode-cli linodes types --text --no-headers --format="id" | xargs | awk '{ print $1 }')
    run linode-cli linodes create \
        --backups_enabled="true" \
        --type="$linode_type" \
        --region us-east \
        --image="$test_image" \
        --root_pass="$random_pass" \
        --text \
        --no-headers

    local linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)

    run linode-cli linodes list --format="id,enabled" \
        --delimiter="," \
        --text \
        --no-headers

    assert_success
    assert_output --partial "$linode_id,True"
}

@test "it should take a snapshot of a linode" {
    local linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)

    if [ "$RUN_LONG_TESTS" = "TRUE" ]; then
        SECONDS=0
        until [[ $(linode-cli linodes view "$linode_id" --format="status" --text --no-headers) = "running" ]]; do
            echo 'still provisioning'
            # Wait 5 seconds before checking status again, to rate-limit ourselves
            sleep 5
            if (( $SECONDS > 180 ));
            then
                assert_failure # Linode failed to boot
                break
            fi
        done

        run linode-cli linodes snapshot $linode_id \
            --label="$snapshot_label" \
            --text \
            --delimiter="," \
            --no-headers

        assert_success
        assert_output --regexp "[0-9]+,pending,snapshot,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,${snapshot_label}"
    else
        skip "Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE"
    fi
}

@test "it should view the snapshot" {
    local linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)

    if [ $RUN_LONG_TESTS  = "TRUE" ]; then
        run linode-cli linodes backups-list "$linode_id" \
            --delimiter="," \
            --text \
            --no-headers
        assert_success

        # assert_output --regexp "[0-9]+,pending,snapshot,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,${snapshot_label}"
        # BUG outputs the backup as json, assertion below asserts that outputs the expected.
        assert_output --regexp "'status':.*'pending"
        assert_output --regexp "'finished':.*None"
        assert_output --regexp "'type':.*'snapshot'"
        assert_output --regexp "'label':.*'$snapshot_label'"
        assert_output --regexp "'region':.*'us-east'"
        assert_output --regexp "'id':.*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]"
    else
        skip "Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE"
    fi
}

# @test "it should restore the linode from a snapshot" {

# }

@test "it should cancel backups" {
    if [ "$TEST_ENVIRONMENT" = "dev" ] || [ $"TEST_ENVIRONMENT" = "test" ]; then
        skip "Skipping backups tests"
    fi

    # Ensure we clean up after, even if the assertion fails
    LAST_TEST="TRUE"

    run linode-cli linodes backups-cancel "$linode_id" \
        --text \
        --no-headers
    assert_success

    clean_linodes="TRUE"
}
