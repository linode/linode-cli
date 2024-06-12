#!/bin/bash

# Fetch the list of LKE cluster IDs
CLUSTER_IDS=$(curl -s -H "Authorization: Bearer $LINODE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://api.linode.com/v4/lke/clusters" | jq -r '.data[].id')

# Check if CLUSTER_IDS is empty
if [ -z "$CLUSTER_IDS" ]; then
    echo "No clusters are present."
    exit 0
fi

for ID in $CLUSTER_IDS; do
    echo "Cluster ID: $ID"

    # Download cluster configuration file
    curl -sH "Authorization: Bearer $LINODE_TOKEN" \
        "https://api.linode.com/v4/lke/clusters/$ID/kubeconfig" | jq -r '.[] | @base64d' > "${ID}_config.yaml"

    # Export downloaded config file for
    export KUBECONFIG="$(pwd)/${ID}_config.yaml"

    echo "Applying Calico Rules to Nodes:"
    ./kubectl get nodes

    ./calicoctl-linux-amd64 patch kubecontrollersconfiguration default --patch='{"spec": {"controllers": {"node": {"hostEndpoint": {"autoCreate": "Enabled"}}}}}'

    ./calicoctl-linux-amd64 apply -f "$(pwd)/lke-policy.yaml"
done
