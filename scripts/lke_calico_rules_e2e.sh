#!/bin/bash

RETRIES=3
DELAY=30

# Function to retry a command with exponential backoff
retry_command() {
    local retries=$1
    local wait_time=60
    shift
    until "$@"; do
        if ((retries == 0)); then
            echo "Command failed after multiple retries. Exiting."
            exit 1
        fi
        echo "Command failed. Retrying in $wait_time seconds..."
        sleep $wait_time
        ((retries--))
        wait_time=$((wait_time * 2))
    done
}

# Fetch the list of LKE cluster IDs
CLUSTER_IDS=$(curl -s -H "Authorization: Bearer $LINODE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://api.linode.com/v4/lke/clusters" | jq -r '.data[].id')

# Check if CLUSTER_IDS is empty
if [ -z "$CLUSTER_IDS" ]; then
    echo "All clusters have been cleaned and properly destroyed. No need to apply inbound or outbound rules"
    exit 0
fi

for ID in $CLUSTER_IDS; do
    echo "Applying Calico rules to nodes in Cluster ID: $ID"

    # Download cluster configuration file with retry
    for ((i=1; i<=RETRIES; i++)); do
        config_response=$(curl -sH "Authorization: Bearer $LINODE_TOKEN" "https://api.linode.com/v4/lke/clusters/$ID/kubeconfig")
        if [[ $config_response != *"kubeconfig is not yet available"* ]]; then
            echo $config_response | jq -r '.[] | @base64d' > "${ID}_config.yaml"
            break
        fi
        echo "Attempt $i to download kubeconfig for cluster $ID failed. Retrying in $DELAY seconds..."
        sleep $DELAY
    done

    if [[ $config_response == *"kubeconfig is not yet available"* ]]; then
        echo "kubeconfig for cluster id:$ID not available after $RETRIES attempts, mostly likely it is an empty cluster. Skipping..."
    else
        # Export downloaded config file
        export KUBECONFIG="$(pwd)/${ID}_config.yaml"

        retry_command $RETRIES kubectl get nodes

        retry_command $RETRIES calicoctl patch kubecontrollersconfiguration default --patch='{"spec": {"controllers": {"node": {"hostEndpoint": {"autoCreate": "Enabled"}}}}}'

        retry_command $RETRIES calicoctl apply -f "$(pwd)/lke-policy.yaml"
    fi
done
