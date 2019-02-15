# Get an available image and set it as an env variable
if [ -z "$test_image" ]; then
    export test_image=$(linode-cli images list --format id --text --no-header | egrep "linode\/.*" | head -n 1)
fi

# Random pass to use persistently thorough test run
if [  -z "$random_pass" ]; then
    export random_pass=$(openssl rand -base64 32)
fi

# A Unique tag to use in tag related tests
if [ -z "$uniqueTag" ]; then
    export uniqueTag="$(date +%s)-tag"
fi

createLinode() {
    local linode_type=$(linode-cli linodes types --text --no-headers --format="id" | xargs | awk '{ print $1 }')
    run bash -c "linode-cli linodes create --type=$linode_type --region us-east --image=$test_image --root_pass=$random_pass"
    assert_success
}

createVolume() {
    timestamp=$(date +%s)
    run bash -c "linode-cli volumes create --label=A$timestamp --size=10 --region=us-east"
    assert_success
}

shutdownLinodes() {
    local linode_ids="( $(linode-cli --text --no-headers linodes list | awk '{ print $1 }' | xargs) )"
    local id

    for id in $linode_ids ; do
        run bash -c "linode-cli linodes shutdown $id"
    done
}

removeLinodes() {
    local linode_ids="( $(linode-cli --text --no-headers linodes list | awk '{ print $1 }' | xargs) )"
    local id

    for id in $linode_ids ; do
        run bash -c "linode-cli linodes delete $id"
    done
}

removeDomains() {
    local domain_ids="( $( linode-cli domains list --format "id" --text --no-headers ) )"
    local id

    for id in $domain_ids ; do
        run bash -c "linode-cli domains delete $id"
        [ "$status" -eq 0 ]
    done
}

removeVolumes() {
    local volume_ids="( $(linode-cli volumes list --text --no-headers --format="id" | xargs) )"
    local id

    for id in $volume_ids ; do
        run bash -c "linode-cli volumes delete $id"
    done
}

removeAll() {
    local entity_ids="( $(linode-cli $1 list --text --no-headers --format="id" | xargs) )"
    local id

    for id in $entity_ids ; do
        run bash -c "linode-cli $1 delete $id"
    done
}

removeUniqueTag() {
    run bash -c "linode-cli tags delete $uniqueTag"
}

createLinodeAndWait() {
    local default_plan=$(linode-cli linodes types --text --no-headers --format="id" | xargs | awk '{ print $1 }')
    local linode_type=${1:-$default_plan}
    run bash -c "linode-cli linodes create --type=$linode_type --region us-east --image=$test_image --root_pass=$random_pass"
    assert_success

    local linode_id=$(linode-cli linodes list --format id --text --no-header | head -n 1)


    until [ $(linode-cli linodes view $linode_id --format="status" --text --no-headers) = "running" ]; do
        echo 'still provisioning'

        # Wait 3 seconds before checking status again, to rate-limit ourselves
        sleep 3
    done
}
