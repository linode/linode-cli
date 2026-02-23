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
        "id",
        "label",
        "region",
        "control_plane.audit_logs_enabled",
        "k8s_version",
        "control_plane.high_availability",
        "tier",
        "apl_enabled",
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
        "id",
        "label",
        "region",
        "control_plane.audit_logs_enabled",
        "k8s_version",
        "control_plane.high_availability",
        "tier",
        "apl_enabled",
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
    headers = [
        "id",
        "label",
        "type",
        "count",
        "autoscaler.enabled",
        "autoscaler.max",
        "autoscaler.min",
        "tags",
    ]
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
    headers = ["id", "instance_id", "pool_id", "status"]
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
        "id",
        "label",
        "type",
        "count",
        "autoscaler.enabled",
        "autoscaler.max",
        "autoscaler.min",
        "tags",
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


def test_create_cluster_with_apl_enabled(monkeypatch):
    """
    Test creating an LKE cluster with apl_enabled=true using v4beta API.
    """
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    label = get_random_text(8) + "_apl_enabled_cluster"

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

    # Create cluster with apl_enabled=true
    cluster_label = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "cluster-create",
            "--region",
            test_region,
            "--label",
            label,
            "--node_pools.type",
            "g6-standard-8",  # APL requires higher specs
            "--node_pools.count",
            "3",  # APL requires minimum 3 nodes
            "--node_pools.disks",
            '[{"type":"ext4","size":1024}]',
            "--k8s_version",
            lke_version,
            "--tier",
            "standard",
            "--apl_enabled",
            "true",
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format=label",
        ]
    )

    assert label == cluster_label

    cluster_id = get_cluster_id(label=cluster_label)

    # Verify apl_enabled is set to true
    res = exec_test_command(
        BASE_CMDS["lke"] + ["cluster-view", cluster_id, "--json"]
    )
    cluster_data = json.loads(res)
    assert cluster_data[0]["apl_enabled"] is True

    delete_target_id(
        target="lke", id=cluster_id, delete_command="cluster-delete"
    )


def test_create_cluster_with_apl_disabled(monkeypatch):
    """
    Test creating an LKE cluster with apl_enabled=false.
    """
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    label = get_random_text(8) + "_apl_disabled_cluster"

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

    # Create cluster with apl_enabled=false
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
            "--apl_enabled",
            "false",
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format=label",
        ]
    )

    assert label == cluster_label

    cluster_id = get_cluster_id(label=cluster_label)

    # Verify apl_enabled is set to false
    res = exec_test_command(
        BASE_CMDS["lke"] + ["cluster-view", cluster_id, "--json"]
    )
    cluster_data = json.loads(res)
    assert cluster_data[0]["apl_enabled"] is False

    delete_target_id(
        target="lke", id=cluster_id, delete_command="cluster-delete"
    )


def test_create_cluster_apl_default(monkeypatch):
    """
    Test creating an LKE cluster without specifying apl_enabled (should default to false).
    """
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    label = get_random_text(8) + "_apl_default_cluster"

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

    # Create cluster without apl_enabled parameter
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

    # Verify apl_enabled defaults to false
    res = exec_test_command(
        BASE_CMDS["lke"] + ["cluster-view", cluster_id, "--json"]
    )
    cluster_data = json.loads(res)
    assert cluster_data[0]["apl_enabled"] is False

    delete_target_id(
        target="lke", id=cluster_id, delete_command="cluster-delete"
    )


def test_update_cluster_enable_apl(lke_cluster, monkeypatch):
    """
    Test updating an existing LKE cluster to enable apl_enabled.
    """
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    cluster_id = lke_cluster

    # Update cluster to enable APL
    res = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "cluster-update",
            cluster_id,
            "--apl_enabled",
            "true",
            "--json",
        ]
    )

    cluster_data = json.loads(res)
    assert cluster_data[0]["apl_enabled"] is True

    # Verify the change persists
    res = exec_test_command(
        BASE_CMDS["lke"] + ["cluster-view", cluster_id, "--json"]
    )
    cluster_data = json.loads(res)
    assert cluster_data[0]["apl_enabled"] is True


def test_update_cluster_disable_apl(monkeypatch):
    """
    Test updating an LKE cluster to disable apl_enabled.
    """
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    # Create a cluster with APL enabled first
    label = get_random_text(8) + "_apl_toggle_cluster"

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
            "g6-dedicated-8",
            "--node_pools.count",
            "3",
            "--node_pools.disks",
            '[{"type":"ext4","size":1024}]',
            "--k8s_version",
            lke_version,
            "--tier",
            "standard",
            "--apl_enabled",
            "true",
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format=label",
        ]
    )

    cluster_id = get_cluster_id(label=cluster_label)

    # Verify APL is enabled
    res = exec_test_command(
        BASE_CMDS["lke"] + ["cluster-view", cluster_id, "--json"]
    )
    cluster_data = json.loads(res)
    assert cluster_data[0]["apl_enabled"] is True

    # Update cluster to disable APL
    res = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "cluster-update",
            cluster_id,
            "--apl_enabled",
            "false",
            "--json",
        ]
    )

    cluster_data = json.loads(res)
    assert cluster_data[0]["apl_enabled"] is False

    # Verify the change persists
    res = exec_test_command(
        BASE_CMDS["lke"] + ["cluster-view", cluster_id, "--json"]
    )
    cluster_data = json.loads(res)
    assert cluster_data[0]["apl_enabled"] is False

    delete_target_id(
        target="lke", id=cluster_id, delete_command="cluster-delete"
    )


def test_list_clusters_includes_apl_enabled(monkeypatch):
    """
    Test that clusters-list includes apl_enabled field for all clusters.
    """
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    # Create two clusters - one with APL enabled, one without
    label_apl_on = get_random_text(8) + "_apl_on"
    label_apl_off = get_random_text(8) + "_apl_off"

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

    # Create cluster with APL enabled
    exec_test_command(
        BASE_CMDS["lke"]
        + [
            "cluster-create",
            "--region",
            test_region,
            "--label",
            label_apl_on,
            "--node_pools.type",
            "g6-dedicated-8",
            "--node_pools.count",
            "3",
            "--node_pools.disks",
            '[{"type":"ext4","size":1024}]',
            "--k8s_version",
            lke_version,
            "--tier",
            "standard",
            "--apl_enabled",
            "true",
            "--text",
            "--no-headers",
            "--format=label",
        ]
    )

    # Create cluster with APL disabled
    exec_test_command(
        BASE_CMDS["lke"]
        + [
            "cluster-create",
            "--region",
            test_region,
            "--label",
            label_apl_off,
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
            "--apl_enabled",
            "false",
            "--text",
            "--no-headers",
            "--format=label",
        ]
    )

    cluster_id_apl_on = get_cluster_id(label=label_apl_on)
    cluster_id_apl_off = get_cluster_id(label=label_apl_off)

    # List all clusters and verify apl_enabled is present
    res = exec_test_command(BASE_CMDS["lke"] + ["clusters-list", "--json"])
    clusters = json.loads(res)

    # Find our test clusters
    apl_on_cluster = next(
        (c for c in clusters if c["id"] == int(cluster_id_apl_on)), None
    )
    apl_off_cluster = next(
        (c for c in clusters if c["id"] == int(cluster_id_apl_off)), None
    )

    assert apl_on_cluster is not None
    assert apl_off_cluster is not None

    assert apl_on_cluster["apl_enabled"] is True
    assert apl_off_cluster["apl_enabled"] is False

    # Cleanup
    delete_target_id(
        target="lke", id=cluster_id_apl_on, delete_command="cluster-delete"
    )
    delete_target_id(
        target="lke", id=cluster_id_apl_off, delete_command="cluster-delete"
    )
