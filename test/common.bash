removeLinodes() {
    local linode_ids="( $(linode-cli --text --no-headers linodes list | awk '{ print $1 }' | xargs) )"
    local id

    for id in $linode_ids ; do
        run bash -c "linode-cli linodes delete $id"
        [ "$status" -eq 0 ]
    done
}

# Get an available image and set it as an env variable
if [ -z "$test_image" ]; then
    export test_image=$(linode-cli images list --format id --text --no-header | head -n 1)
fi