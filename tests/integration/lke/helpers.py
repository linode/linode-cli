import json

from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
)


def get_lke_version_id():
    version_id = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "versions-list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()

    first_id = version_id[0]

    return first_id


def get_node_pool_id(cluster_id):
    cluster_id
    nodepool_id = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "pools-list",
            cluster_id,
            "--text",
            "--no-headers",
            "--format",
            "id",
        ]
    ).splitlines()

    first_id = nodepool_id[0]

    return first_id


def get_pool_nodesid(cluster_id):
    response = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "pools-list",
            cluster_id,
            "--json",
        ]
    )

    nodepools = json.loads(response)

    return nodepools[0]["nodes"][0]["id"]


def get_lke_enterprise_id():
    enterprise_tier_info_list = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "tiered-versions-list",
            "enterprise",
            "--json",
        ]
    )

    parsed = json.loads(enterprise_tier_info_list)

    enterprise_ti = parsed[0]

    return enterprise_ti.get("id")


def get_cluster_id(label: str):
    cluster_id = exec_test_command(
        [
            "linode-cli",
            "lke",
            "clusters-list",
            "--text",
            "--format=id",
            "--no-headers",
            "--label",
            label,
        ]
    )

    return cluster_id
