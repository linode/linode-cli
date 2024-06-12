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

    # Sleep needed here for proper deletion of linodes that are related to lke cluster
    time.sleep(15)

    remove_lke_clusters()


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


def test_beta_view(test_version_id):
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
