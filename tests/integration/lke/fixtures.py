import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
)
from tests.integration.lke.helpers import get_cluster_id


@pytest.fixture(scope="session")
def lke_cluster():
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
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format",
            "label",
            "--no-defaults",
        ]
    )

    cluster_id = get_cluster_id(label=cluster_label)

    yield cluster_id

    delete_target_id(
        target="lke", id=cluster_id, delete_command="cluster-delete"
    )


@pytest.fixture(scope="session")
def node_pool(lke_cluster):
    cluster_id = lke_cluster

    node_pool_id = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "pool-create",
            cluster_id,
            "--count",
            "1",
            "--type",
            "g6-standard-4",
            "--labels",
            '{ "example.com/my-app":"team1" }',
            "--text",
            "--format=id",
            "--no-headers",
        ]
    )

    yield node_pool_id


@pytest.fixture(scope="session")
def lke_cluster_acl():
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
            "--control_plane.high_availability",
            "true",
            "--control_plane.acl.enabled",
            "true",
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format",
            "label",
            "--no-defaults",
        ]
    )

    cluster_id = get_cluster_id(label=cluster_label)

    yield cluster_id

    delete_target_id(
        target="lke", id=cluster_id, delete_command="cluster-delete"
    )
