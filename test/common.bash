removeLinodes() {
    local linode_ids="( $(linode-cli --text --no-headers linodes list | awk '{ print $1 }' | xargs) )"
    local id

    for id in $linode_ids ; do
        run bash -c "linode-cli linodes delete $id"
        [ "$status" -eq 0 ]
    done
}
