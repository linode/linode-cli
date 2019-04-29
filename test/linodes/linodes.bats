#!/usr/bin/env bats

load '../test_helper/bats-support/load'
load '../test_helper/bats-assert/load'
load '../common'

##################################################################
#  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
#  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
##################################################################

setup() {
    suiteName="linodes"
    setToken "$suiteName"
}

teardown() {
    if [ "$LAST_TEST" = "TRUE" ]; then
        clearToken "$suiteName"
        rm .tmp-linode-tag
    fi
}

@test "it should create linodes with a label" {
    run linode-cli linodes create \
        --type g6-standard-2 \
        --region us-east \
        --image $test_image \
        --label cli-1 \
        --root_pass $random_pass \
        --text \
        --delimiter "," \
        --no-headers \
        --format 'label,region,type,image' \
        --no-defaults

    assert_output --regexp "cli-1,us-east,g6-standard-2,$test_image"
}

@test "it should view the linode configuration" {
    linode_id=$(linode-cli --text --no-headers linodes list | awk '{ print $1 }' | xargs)
    run linode-cli linodes view "$linode_id" \
        --text \
        --delimiter "," \
        --no-headers \
        --format 'id,label,region,type,image' \
        --no-defaults

    assert_output --regexp "$linode_id,cli-1,us-east,g6-standard-2,$test_image"
}

@test "it should create a linode with the minimum required props" {
    run linode-cli linodes create \
        --type g6-standard-2 \
        --region us-east \
        --root_pass $random_pass \
        --no-defaults \
        --text \
        --delimiter "," \
        --no-headers \
        --format 'id,region,type'

    assert_output --regexp "[0-9]+,us-east,g6-standard-2"
    run removeLinodes
}

@test "it should fail to create a linode without a root_pass" {
    run linode-cli linodes create \
        --type g6-standard-2 \
        --region us-east \
        --image $test_image \
        --no-defaults \
        --text \
        --no-headers

    assert_failure
    assert_output --partial 'Request failed: 400'
    assert_output --partial 'root_pass	root_pass is required'
}

@test "it should create a linode without an image and not boot" {
    local linode_type=$(linode-cli linodes types --text --no-headers --format="id" | xargs | awk '{ print $1 }')
    local linode_region=$(linode-cli regions list --format="id"  --text --no-headers | xargs | awk '{ print $1 }')
    run linode-cli linodes create \
        --no-defaults \
        --label='cli-2' \
        --type=$linode_type \
        --region=$linode_region \
        --root_pass $random_pass
    local linode_id=$(linode-cli linodes list --format="id" --text --no-headers)

    SECONDS=0
    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "offline" ]; do
        if (( $SECONDS > 180 )); then
            echo "Timeout elapsed! Linode did not initialize in time"
            assert_failure  # This will fail the test
            break
        fi

        sleep 5
        echo 'still setting up'
    done

    run linode-cli linodes view $linode_id --format="status" --text --no-headers
    assert_success
    assert_output "offline"
}

@test "it should list linodes" {
    run linode-cli linodes list \
        --no-headers \
        --format 'label' \
        --text

    assert_output --partial 'cli-2'
}

@test "it should add a tag a linode" {
    local linode_id=$(linode-cli --text --no-headers linodes list | awk '{ print $1 }' | xargs)
    echo "export tag=$uniqueTag" > .tmp-linode-tag

    run linode-cli linodes update $linode_id \
        --tags=$uniqueTag \
        --format 'tags' \
        --text \
        --no-headers

    assert_success
    assert_output $uniqueTag
}

@test "it should remove all linodes" {
    LAST_TEST="TRUE"

    source .tmp-linode-tag
    run removeLinodes
    run removeTag "$tag"
}
