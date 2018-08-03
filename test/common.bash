removeLinodes() {
    local linode_ids="( $(linode-cli --text --no-headers linodes list | awk '{ print $1 }' | xargs) )"
    local id

    for id in $linode_ids ; do
        run bash -c "linode-cli linodes delete $id"
        [ "$status" -eq 0 ]
    done
}

removeDomains() {
    local domain_ids="( $( linode-cli domains list --format "id" --text --no-headers ))"
    local id

    for id in $domain_ids ; do
        run bash -c "linode-cli domains delete $id"
        [ "$status" -eq 0 ]
    done
}

# Get an available image and set it as an env variable
if [ -z "$test_image" ]; then
    export test_image=$(linode-cli images list --format id --text --no-header | egrep "linode\/.*" | head -n 1)
fi

if [  -z "$random_pass" ]; then
	export random_pass=$(openssl rand -base64 32)
fi
