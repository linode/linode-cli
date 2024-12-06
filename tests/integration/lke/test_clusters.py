import pytest

from tests.integration.helpers import (
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
    get_cluster_id,
    get_random_region_with_caps,
    get_random_text,
    retry_exec_test_command_with_delay,
)

BASE_CMD = ["linode-cli", "lke"]


def get_lke_version_id():
    version_id = (
        exec_test_command(
            BASE_CMD
            + [
                "versions-list",
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )

    first_id = version_id[0]

    return first_id


def get_node_pool_id(cluster_id):
    cluster_id
    nodepool_id = (
        exec_test_command(
            BASE_CMD
            + [
                "pools-list",
                cluster_id,
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )

    first_id = nodepool_id[0]

    return first_id


def get_pool_nodesid(cluster_id):
    cluster_id
    nodepool_id = (
        exec_test_command(
            BASE_CMD
            + [
                "pools-list",
                cluster_id,
                "--text",
                "--no-headers",
                "--format",
                "nodes.id",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )

    first_id = nodepool_id[0]

    return first_id


@pytest.fixture
def test_lke_cluster():
    label = get_random_text(8) + "_cluster"

    test_region = get_random_region_with_caps(
        required_capabilities=["Linodes", "Kubernetes"]
    )
    lke_version = (
        exec_test_command(
            BASE_CMD
            + [
                "versions-list",
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()[0]
    )

    cluster_label = (
        exec_test_command(
            BASE_CMD
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
                "--text",
                "--delimiter",
                ",",
                "--no-headers",
                "--format",
                "label",
                "--no-defaults",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    cluster_id = get_cluster_id(label=cluster_label)

    yield cluster_id

    delete_target_id(
        target="lke", id=cluster_id, delete_command="cluster-delete"
    )


@pytest.mark.smoke
def test_deploy_an_lke_cluster():
    label = get_random_text(8) + "_cluster"

    test_region = get_random_region_with_caps(
        required_capabilities=["Linodes", "Kubernetes"]
    )
    lke_version = (
        exec_test_command(
            BASE_CMD
            + [
                "versions-list",
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()[0]
    )

    cluster_label = (
        exec_test_command(
            BASE_CMD
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
                "--text",
                "--delimiter",
                ",",
                "--no-headers",
                "--format=label",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert label == cluster_label

    cluster_id = get_cluster_id(label=cluster_label)

    delete_target_id(
        target="lke", id=cluster_id, delete_command="cluster-delete"
    )


def test_lke_cluster_list():
    res = (
        exec_test_command(
            BASE_CMD + ["clusters-list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["label", "k8s_version"]
    assert_headers_in_lines(headers, lines)


def test_view_lke_cluster(test_lke_cluster):
    cluster_id = test_lke_cluster

    res = (
        exec_test_command(
            BASE_CMD + ["cluster-view", cluster_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["label", "k8s_version"]
    assert_headers_in_lines(headers, lines)


def test_update_kubernetes_cluster(test_lke_cluster):
    cluster_id = test_lke_cluster
    new_label = get_random_text(5) + "_updated_cluster"

    updated_label = (
        exec_test_command(
            BASE_CMD
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
        .stdout.decode()
        .rstrip()
    )

    assert new_label == updated_label


def test_list_kubernetes_endpoint(test_lke_cluster):
    cluster_id = test_lke_cluster
    res = (
        retry_exec_test_command_with_delay(
            BASE_CMD
            + ["api-endpoints-list", cluster_id, "--text", "--delimiter=,"],
            retries=3,
            delay=30,
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["endpoint"]
    assert_headers_in_lines(headers, lines)


def test_cluster_dashboard_url(test_lke_cluster):
    cluster_id = test_lke_cluster
    res = (
        exec_test_command(
            BASE_CMD
            + ["cluster-dashboard-url", cluster_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["url"]
    assert_headers_in_lines(headers, lines)


def test_node_pool_list(test_lke_cluster):
    cluster_id = test_lke_cluster
    res = (
        exec_test_command(
            BASE_CMD + ["pools-list", cluster_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["nodes.id", "nodes.instance_id"]
    assert_headers_in_lines(headers, lines)


def test_view_pool(test_lke_cluster):
    cluster_id = test_lke_cluster
    node_pool_id = get_node_pool_id(cluster_id)

    res = (
        exec_test_command(
            BASE_CMD
            + ["pool-view", cluster_id, node_pool_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )

    lines = res.splitlines()
    headers = ["type", "labels.value"]
    assert_headers_in_lines(headers, lines)


def test_update_node_pool(test_lke_cluster):
    cluster_id = test_lke_cluster
    node_pool_id = get_node_pool_id(cluster_id)
    new_label = get_random_text(8) + "updated_pool"

    result = (
        exec_test_command(
            BASE_CMD
            + [
                "pool-update",
                cluster_id,
                node_pool_id,
                "--count",
                "5",
                "--labels.value",
                new_label,
                "--text",
                "--no-headers",
                "--format=label",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert new_label in result


def test_view_node(test_lke_cluster):
    cluster_id = test_lke_cluster
    node_pool_id = get_pool_nodesid(cluster_id)

    res = (
        exec_test_command(
            BASE_CMD
            + ["node-view", cluster_id, node_pool_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )

    lines = res.splitlines()
    headers = ["id", "id,instance_id,status"]
    assert_headers_in_lines(headers, lines)


def test_version_view():
    version_id = get_lke_version_id()
    res = (
        exec_test_command(
            BASE_CMD + ["version-view", version_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["id"]
    assert_headers_in_lines(headers, lines)


def test_list_lke_types():
    types = (
        exec_test_command(
            BASE_CMD
            + [
                "types",
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "price.hourly", "price.monthly", "transfer"]
    lines = types.splitlines()

    assert_headers_in_lines(headers, lines)
    assert "LKE Standard Availability" in types
    assert "LKE High Availability" in types


def test_create_node_pool_default_to_disk_encryption_enabled(test_lke_cluster):
    cluster_id = test_lke_cluster

    result = (
        exec_test_command(
            BASE_CMD
            + [
                "pool-create",
                cluster_id,
                "--count",
                "1",
                "--type",
                "g6-standard-4",
                "--text",
                "--format=id,disk_encryption,type",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert "enabled" in result
    assert "g6-standard-4" in result


@pytest.fixture
def test_node_pool(test_lke_cluster):
    cluster_id = test_lke_cluster

    node_pool_id = (
        exec_test_command(
            BASE_CMD
            + [
                "pool-create",
                cluster_id,
                "--count",
                "1",
                "--type",
                "g6-standard-4",
                "--text",
                "--format=id",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield node_pool_id


def test_update_autoscaler(test_lke_cluster, test_node_pool):
    cluster_id = test_lke_cluster
    node_pool_id = test_node_pool

    result = (
        exec_test_command(
            BASE_CMD
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
        .stdout.decode()
        .rstrip()
    )

    headers = [
        "autoscaler.enabled",
        "autoscaler.max",
        "autoscaler.min",
        "count",
        "disk_encryption",
        "id",
        "labels.key",
        "labels.value",
        "tags",
        "taints",
        "type",
    ]

    assert_headers_in_lines(headers, result.splitlines())

    assert "3" in result
    assert "1" in result


def test_kubeconfig_view(test_lke_cluster):
    cluster_id = test_lke_cluster

    kubeconfig = (
        retry_exec_test_command_with_delay(
            BASE_CMD
            + [
                "kubeconfig-view",
                cluster_id,
                "--text",
            ],
            retries=5,
            delay=60,
        )
        .stdout.decode()
        .strip()
    )

    header = ["kubeconfig"]

    assert_headers_in_lines(header, kubeconfig.splitlines())

    assert kubeconfig


def test_cluster_nodes_recycle(test_lke_cluster):
    cluster_id = test_lke_cluster

    exec_test_command(BASE_CMD + ["cluster-nodes-recycle", cluster_id])
