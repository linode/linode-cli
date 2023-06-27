import time
from random import randint

import pytest

from tests.integration.helpers import exec_test_command, remove_lke_clusters

BASE_CMD = ["linode-cli", "lke"]


@pytest.fixture(autouse=True)
def setup_test_clusters():
    yield "setup"
    remove_lke_clusters()


@pytest.mark.smoke
def test_deploy_an_lke_cluster():
    timestamp = str(int(time.time()) + randint(10, 1000))
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
            "us-east",
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

    assert label + ",us-east," + lke_version in result

    # Sleep needed here for proper deletion of linodes that are related to lke cluster
    time.sleep(15)

    remove_lke_clusters()
