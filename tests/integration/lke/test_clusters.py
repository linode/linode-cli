import time

import pytest

from tests.integration.helpers import (
    assert_headers_in_lines,
    exec_test_command,
    remove_lke_clusters,
)

BASE_CMD = ["linode-cli", "lke"]


@pytest.mark.smoke
def test_deploy_an_lke_cluster():
    timestamp = str(time.time_ns())
    label = "cluster_test" + timestamp

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

    result = exec_test_command(
        BASE_CMD
        + [
            "cluster-create",
            "--region",
            "us-ord",
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
            "label,region,k8s_version",
            "--no-defaults",
        ]
    ).stdout.decode()
    assert label + ",us-ord," + lke_version in result


@pytest.fixture
def get_cluster_id():
    cluster_id = (
        exec_test_command(
            BASE_CMD
            + [
                "clusters-list",
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
    first_id = cluster_id[0]
    yield first_id


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


def test_view_lke_cluster(get_cluster_id):
    cluster_id = get_cluster_id

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


def test_update_kubernetes_cluster(get_cluster_id):
    cluster_id = get_cluster_id
    new_label = "cluster_test" + str(time.time_ns())
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


@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_list_kubernetes_endpoint(get_cluster_id):
    cluster_id = get_cluster_id
    res = (
        exec_test_command(
            BASE_CMD
            + ["api-endpoints-list", cluster_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["endpoint"]
    assert_headers_in_lines(headers, lines)


def test_cluster_dashboard_url(get_cluster_id):
    cluster_id = get_cluster_id
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


@pytest.fixture
def get_node_pool_id(get_cluster_id):
    cluster_id = get_cluster_id
    nodepool_id = (
        exec_test_command(
            BASE_CMD
            + [
                "pools-list",
                cluster_id,
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
    first_id = nodepool_id[0]
    yield first_id


def test_node_pool_list(get_cluster_id):
    cluster_id = get_cluster_id
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


def test_view_pool(get_cluster_id, get_node_pool_id):
    cluster_id = get_cluster_id
    node_pool_id = get_node_pool_id
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


@pytest.mark.skip(reason="BUG TPT-TPT-3145")
def test_update_node_pool(get_cluster_id, get_node_pool_id):
    cluster_id = get_cluster_id
    node_pool_id = get_node_pool_id
    new_label = "cluster_test" + str(time.time_ns())
    updated_count = (
        exec_test_command(
            BASE_CMD
            + [
                "pool-update",
                cluster_id,
                node_pool_id,
                "--count",
                "5",
                "--label.value",
                new_label,
                "--text",
                "--no-headers",
                "--format=label",
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    assert new_label == updated_count


@pytest.mark.skip(reason="BUG TPT-TPT-3145")
def test_view_node(get_cluster_id, get_node_pool_id):
    cluster_id = get_cluster_id
    node_pool_id = get_node_pool_id
    res = (
        exec_test_command(
            BASE_CMD
            + ["node-view", cluster_id, node_pool_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["type", "labels.value"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def test_version_id():
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
    yield first_id


def test_version_view(test_version_id):
    version_id = test_version_id
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
    # Sleep needed here for proper deletion of linodes that are related to lke cluster
    time.sleep(5)
    remove_lke_clusters()
