"""
This plugin allows the option to merge an LKE Cluster's kubeconfig to a desired location.

Usage:

   linode-cli get-kubeconfig --id <cluster-id> --kubeconfig /path/to/config/file
"""

import argparse
import base64
import sys
from pathlib import Path

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
        print("Either --label or --id must be used.", file=sys.stderr)
        sys.exit(1)

    # Load the specified cluster's kubeconfig and the current kubeconfig
    cluster_config = yaml.safe_load(
        base64.b64decode(kubeconfig["kubeconfig"]).decode()
    )
    current_config = None

    kubeconfig_path = Path(parsed.kubeconfig).expanduser()
    if kubeconfig_path.exists():
        current_config = _load_config(kubeconfig_path)

    # If there is no current kubeconfig, dump the cluster config to the specified file location.
    # If there is a current kubeconfig, merge it with the cluster's kubeconfig
    cluster_config = (
        _merge_dict(current_config, cluster_config)
        if current_config is not None
        else cluster_config
    )
    if parsed.dry_run:
        print(cluster_config)
    else:
        _dump_config(kubeconfig_path, cluster_config)


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
    with open(filepath, "r", encoding="utf-8") as file_descriptor:
        data = yaml.load(file_descriptor, Loader=yaml.Loader)

    if not data:
        print(f"Could not load file at {filepath}", file=sys.stderr)
        sys.exit(1)

    return data


# Dumps data to a yaml file
def _dump_config(filepath, data):
    Path.mkdir(filepath.parent, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as file_descriptor:
        yaml.dump(data, file_descriptor)


# Merges the lists in the provided dicts. If non-list properties of the two
# dicts differ, uses the value from the first dict.
def _merge_dict(dict_1, dict_2):
    # Return a new dict to prevent any accidental mutations
    result = {}

    for key in dict_1:
        if not isinstance(dict_1[key], list):
            result[key] = dict_1[key]
            continue

        merge_map = {sub["name"]: sub for sub in dict_1[key]}

        for sub in dict_2[key]:
            # If the name is already in the merge map, skip
            if sub["name"] in merge_map:
                continue

            merge_map[sub["name"]] = sub

        # Convert back to a list
        result[key] = list(merge_map.values())

    return result
