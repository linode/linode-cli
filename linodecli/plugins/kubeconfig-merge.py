"""
This plugin allows the option to merge an LKE Cluster's kubeconfig to a desired location.

Usage:

   linode-cli get-kubeconfig --id <cluster-id> --kubeconfig /path/to/config/file
"""

import argparse
import base64
import sys
import json
import yaml


PLUGIN_BASE = "linode-cli get-kubeconfig"

def call(args, context):
    """
    The entrypoint for this plugin
    """
    parser = argparse.ArgumentParser(PLUGIN_BASE, add_help=True)

    group = parser.add_mutually_exclusive_group()

    parser.add_argument(
        "--kubeconfig",
        metavar="KUBECONFIG",
        nargs="?",
        help="",
        default="~/.kube/config",
    )
    parser.add_argument(
        "--dry-run",
        metavar="DRY_RUN",
        help="",
    )
    group.add_argument(
        "--label",
        metavar="LABEL",
        nargs="?",
        help="",
    )
    group.add_argument(
        "--id",
        metavar="ID",
        nargs="?",
        help="",
    )

    parsed = parser.parse_args(args)

    # If --id was used, fetch the kubeconfig using the provided id
    if parsed.id:
        code, kubeconfig = context.client.call_operation(
            "lke", "kubeconfig-view", args=[parsed.id]
        )

        if code != 200:
            print(f"Error retrieving kubeconfig: {code}")
            sys.exit(1)

    # If --label was used, fetch the kubeconfig using the provided label
    elif parsed.label:
       kubeconfig = _get_kubeconfig_by_label(parsed.label, context.client)

    # Load the specified cluster's kubeconfig and the current kubeconfig
    clusterConfig = json.loads(base64.standard_b64decode(kubeconfig["kubeconfig"]))
    currentConfig = _load_config(parsed.kubeconfig)

    # If there is no current kubeconfig, dump the cluster config to the specified file location.
    # If there is a current kubeconfig, merge it with the cluster's kubeconfig
    if not currentConfig:
        _dump_config(parsed.kubeconfig, clusterConfig)
    else:
        _dump_config(parsed.kubeconfig, clusterConfig.update(currentConfig))



# Fetches the kubeconfig of the lke cluster with the specified label
def _get_kubeconfig_by_label(cluster_label, client):
    """
    Returns the LKE Cluster with the given ID
    """

    code, cluster = client.call_operation(
        "lke", "clusters-list", args=["--label", cluster_label]
    )

    if code != 200:
        print(f"Error retrieving cluster: {code}")
        sys.exit(1)

    code, kubeconfig = client.call_operation(
        "lke", "kubeconfig-view", args=[cluster["id"]]
    )

    if code != 200:
        print(f"Error retrieving kubeconfig: {code}")
        sys.exit(1)

    return kubeconfig

# Loads a yaml file
def _load_config(filepath):
    with open(filepath, "r")as file_descriptor:
        data = yaml.load(file_descriptor)
    return data

# Dumps data to a yaml file
def _dump_config(filepath, data):
    with open(filepath, "w") as file_descriptor:
        yaml.dump(data, file_descriptor)