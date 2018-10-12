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

# Get an available image and set it as an env variable
if [ -z "$test_image" ]; then
    export test_image=$(linode-cli images list --format id --text --no-header | egrep "linode\/.*" | head -n 1)
fi

if [  -z "$random_pass" ]; then
	export random_pass=$(openssl rand -base64 32)
fi
