"""
This plugin allows the option to merge an LKE Cluster's kubeconfig to a desired location.

Usage:

   linode-cli get-kubeconfig --id <cluster-id> --kubeconfig /path/to/config/file
"""

import argparse
import base64
import os
import sys

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
        help="Path to kubeconfig file. If omitted, ~/.kube/config will be used.",
        default="~/.kube/config",
    )
    parser.add_argument(
        "--dry-run",
        default=False,
        const=True,
        nargs="?",
        help="Print resulting merged kubeconfig instead of merging.",
    )
    group.add_argument(
        "--label",
        metavar="LABEL",
        nargs="?",
        help="Label for desired cluster. If omitted, the ID must be provided.",
    )
    group.add_argument(
        "--id",
        metavar="ID",
        nargs="?",
        help="ID for desired cluster. If omitted, the Label must be provided.",
    )

    parsed = parser.parse_args(args)

    # If --id was used, fetch the kubeconfig using the provided id
    if parsed.id:
        code, kubeconfig = context.client.call_operation(
            "lke", "kubeconfig-view", args=[parsed.id]
        )

        if code != 200:
            print(f"Error retrieving kubeconfig: {code}", file=sys.stderr)
            sys.exit(1)

    # If --label was used, fetch the kubeconfig using the provided label
    elif parsed.label:
        kubeconfig = _get_kubeconfig_by_label(parsed.label, context.client)
    else:
        print(f"Either --label or --id must be used.", file=sys.stderr)
        sys.exit(1)

    # Load the specified cluster's kubeconfig and the current kubeconfig
    clusterConfig = yaml.safe_load(
        base64.b64decode(kubeconfig["kubeconfig"]).decode()
    )
    currentConfig = None

    if os.path.exists(os.path.expanduser(parsed.kubeconfig)):
        currentConfig = _load_config(os.path.expanduser(parsed.kubeconfig))

    # If there is no current kubeconfig, dump the cluster config to the specified file location.
    # If there is a current kubeconfig, merge it with the cluster's kubeconfig
    if not currentConfig:
        if parsed.dry_run:
            print(clusterConfig)
        else:
            _dump_config(os.path.expanduser(parsed.kubeconfig), clusterConfig)
    else:
        if parsed.dry_run:
            print(_merge_dict(currentConfig, clusterConfig))
        else:
            _dump_config(
                os.path.expanduser(parsed.kubeconfig),
                _merge_dict(currentConfig, clusterConfig),
            )


# Fetches the kubeconfig of the lke cluster with the specified label
def _get_kubeconfig_by_label(cluster_label, client):
    """
    Returns the LKE Cluster with the given Label
    """

    code, cluster = client.call_operation(
        "lke", "clusters-list", args=["--label", cluster_label]
    )

    if code != 200:
        print(f"Error retrieving cluster: {code}", file=sys.stderr)
        sys.exit(1)

    if len(cluster["data"]) == 0:
        print(
            f"Cluster with label {cluster_label} does not exist.",
            file=sys.stderr,
        )
        sys.exit(1)

    code, kubeconfig = client.call_operation(
        "lke", "kubeconfig-view", args=[str(cluster["data"][0]["id"])]
    )

    if code != 200:
        print(f"Error retrieving kubeconfig: {code}", file=sys.stderr)
        sys.exit(1)

    return kubeconfig


# Loads a yaml file
def _load_config(filepath):
    with open(filepath, "r") as file_descriptor:
        data = yaml.load(file_descriptor, Loader=yaml.Loader)

    if not data:
        print(f"Could not load file at {filepath}", file=sys.stderr)
        sys.exit(1)

    return data


# Dumps data to a yaml file
def _dump_config(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as file_descriptor:
        yaml.dump(data, file_descriptor)


# Merges the lists in the provided dicts. If non-list properties of the two
# dicts differ, uses the value from the first dict.
def _merge_dict(dict_1, dict_2):
    for key in dict_1:
        if isinstance(dict_1[key], list):
            # Extract names of each list item for both dicts
            dict1_names = [sub["name"] for sub in dict_1[key]]
            dict2_names = [sub["name"] for sub in dict_2[key]]

            new_entries = []

            # Add all dict_2 entries with unique names to new_entries
            for i in range(len(dict2_names)):
                if dict2_names[i] not in dict1_names:
                    new_entries.append(dict_2[key][i])

            # Concat dict_1 list with new_entries and update dict_1 list to concatenated list
            merged = dict_1[key] + new_entries
            dict_1[key] = merged

    return dict_1
