import json

import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
    retry_exec_test_command_with_delay,
)
from tests.integration.lke.fixtures import lke_cluster, node_pool  # noqa: F401
from tests.integration.lke.helpers import (
    get_cluster_id,
    get_lke_version_id,
    get_node_pool_id,
    get_pool_nodesid,
)


@pytest.mark.smoke
def test_deploy_an_lke_cluster():
    label = get_random_text(8) + "_cluster"

    test_region = get_random_region_with_caps(
        required_capabilities=["Linodes", "Kubernetes"]
    )
    lke_version = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "versions-list",
            "--text",
            "--no-headers",
        ]
    ).splitlines()[0]

    cluster_label = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "cluster-create",
            "--region",
            test_region,
            "--label",
            label,
            "--node_pools.type",
            "g6-standard-1",
            "--node_pools.count",
            "1",
            "--node_pools.disks",
            '[{"type":"ext4","size":1024}]',
            "--k8s_version",
            lke_version,
            "--tier",
            "standard",
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format=label",
        ]
    )

    assert label == cluster_label

    cluster_id = get_cluster_id(label=cluster_label)

    delete_target_id(
        target="lke", id=cluster_id, delete_command="cluster-delete"
    )


def test_lke_cluster_list():
    res = exec_test_command(
        BASE_CMDS["lke"] + ["clusters-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = [
        "label",
        "k8s_version",
        "tier",
        "apl_enabled",
        "vpc_id",
        "subnet_id",
        "stack_type",
    ]
    assert_headers_in_lines(headers, lines)


def test_view_lke_cluster(lke_cluster):
    cluster_id = lke_cluster

    res = exec_test_command(
        BASE_CMDS["lke"]
        + ["cluster-view", cluster_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = [
        "label",
        "k8s_version",
        "tier",
        "apl_enabled",
        "vpc_id",
        "subnet_id",
        "stack_type",
    ]
    assert_headers_in_lines(headers, lines)


def test_update_kubernetes_cluster(lke_cluster):
    cluster_id = lke_cluster
    new_label = get_random_text(5) + "_updated_cluster"

    updated_label = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "cluster-update",
            cluster_id,
            "--label",
            new_label,
            "--text",
            "--no-headers",
            "--format=label",
        ]
    )

    assert new_label == updated_label


def test_list_kubernetes_endpoint(lke_cluster):
    cluster_id = lke_cluster
    res = retry_exec_test_command_with_delay(
        BASE_CMDS["lke"]
        + ["api-endpoints-list", cluster_id, "--text", "--delimiter=,"],
        retries=3,
        delay=30,
    )
    lines = res.splitlines()

    headers = ["endpoint"]
    assert_headers_in_lines(headers, lines)


def test_cluster_dashboard_url(lke_cluster):
    cluster_id = lke_cluster
    res = exec_test_command(
        BASE_CMDS["lke"]
        + ["cluster-dashboard-url", cluster_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["url"]
    assert_headers_in_lines(headers, lines)


def test_node_pool_list(lke_cluster):
    cluster_id = lke_cluster
    res = exec_test_command(
        BASE_CMDS["lke"] + ["pools-list", cluster_id, "--json"]
    )
    data = json.loads(res)

    for pool in data:
        for node in pool.get("nodes", []):
            assert "id" in node
            assert "instance_id" in node


def test_view_pool(lke_cluster):
    cluster_id = lke_cluster
    node_pool_id = get_node_pool_id(cluster_id)

    res = exec_test_command(
        BASE_CMDS["lke"]
        + ["pool-view", cluster_id, node_pool_id, "--text", "--delimiter=,"]
    )

    lines = res.splitlines()
    headers = ["type", "labels", "k8s_version", "label"]
    assert_headers_in_lines(headers, lines)


def test_update_node_pool(lke_cluster):
    cluster_id = lke_cluster
    node_pool_id = get_node_pool_id(cluster_id)
    new_value = get_random_text(8) + "updated_pool"

    result = json.loads(
        exec_test_command(
            BASE_CMDS["lke"]
            + [
                "pool-update",
                cluster_id,
                node_pool_id,
                "--count",
                "5",
                "--labels",
                json.dumps({"label-key": new_value}),
                "--taints",
                '[{"key": "test-key", "value": "test-value", "effect": "NoSchedule"}]',
                "--json",
            ]
        )
    )

    assert result[0]["labels"] == {"label-key": new_value}

    assert result[0]["taints"] == [
        {
            "key": "test-key",
            "value": "test-value",
            "effect": "NoSchedule",
        }
    ]

    # Reset the values for labels and taints (TPT-3665)
    result = json.loads(
        exec_test_command(
            BASE_CMDS["lke"]
            + [
                "pool-update",
                cluster_id,
                node_pool_id,
                "--labels",
                "{}",
                "--taints",
                "[]",
                "--json",
            ]
        )
    )

    assert result[0]["labels"] == {}
    assert result[0]["taints"] == []


def test_view_node(lke_cluster):
    cluster_id = lke_cluster
    node_pool_id = get_pool_nodesid(cluster_id)

    res = exec_test_command(
        BASE_CMDS["lke"]
        + ["node-view", cluster_id, node_pool_id, "--text", "--delimiter=,"]
    )

    lines = res.splitlines()
    headers = ["id", "id,instance_id,status"]
    assert_headers_in_lines(headers, lines)


def test_version_view():
    version_id = get_lke_version_id()
    res = exec_test_command(
        BASE_CMDS["lke"]
        + ["version-view", version_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["id"]
    assert_headers_in_lines(headers, lines)


def test_list_lke_types():
    types = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "types",
            "--text",
        ]
    )

    headers = ["id", "label", "price.hourly", "price.monthly", "transfer"]
    lines = types.splitlines()

    assert_headers_in_lines(headers, lines)
    assert "LKE Standard Availability" in types
    assert "LKE High Availability" in types


def test_create_node_pool_has_disk_encryption_field_set(lke_cluster):
    cluster_id = lke_cluster

    result = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "pool-create",
            cluster_id,
            "--count",
            "1",
            "--type",
            "g6-standard-4",
            "--text",
            "--format=id,disk_encryption,type",
            # "--no-headers",
        ]
    )
    lines = result.splitlines()
    headers = lines[0].split()
    values = lines[1].split()

    # Build a dict for easier access
    pool_info = dict(zip(headers, values))

    disk_encryption_status = pool_info.get("disk_encryption")

    assert disk_encryption_status in ("enabled", "disabled")
    assert "g6-standard-4" in result


def test_update_autoscaler(lke_cluster, node_pool):
    cluster_id = lke_cluster
    node_pool_id = node_pool

    result = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "pool-update",
            cluster_id,
            node_pool_id,
            "--autoscaler.enabled",
            "true",
            "--autoscaler.min",
            "1",
            "--autoscaler.max",
            "3",
            "--text",
        ]
    )

    headers = [
        "autoscaler.enabled",
        "autoscaler.max",
        "autoscaler.min",
        "count",
        "disk_encryption",
        "id",
        "labels",
        "tags",
        "taints",
        "type",
    ]

    assert_headers_in_lines(headers, result.splitlines())

    assert "3" in result
    assert "1" in result


def test_kubeconfig_view(lke_cluster):
    cluster_id = lke_cluster

    kubeconfig = retry_exec_test_command_with_delay(
        BASE_CMDS["lke"]
        + [
            "kubeconfig-view",
            cluster_id,
            "--text",
        ],
        retries=5,
        delay=60,
    )

    header = ["kubeconfig"]

    assert_headers_in_lines(header, kubeconfig.splitlines())

    assert kubeconfig


def test_cluster_nodes_recycle(lke_cluster):
    cluster_id = lke_cluster

    exec_test_command(BASE_CMDS["lke"] + ["cluster-nodes-recycle", cluster_id])
