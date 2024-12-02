# │ cluster-acl-delete    │ Delete the control plane access control list. │
# │ cluster-acl-update    │ Update the control plane access control list. │
# │ cluster-acl-view      │ Get the control plane access control list.    │
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


@pytest.fixture
def test_lke_cluster_acl():
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
        .stdout.decode()
        .rstrip()
    )

    cluster_id = get_cluster_id(label=cluster_label)

    yield cluster_id

    delete_target_id(
        target="lke", id=cluster_id, delete_command="cluster-delete"
    )


def test_cluster_acl_view(test_lke_cluster_acl):
    cluster_id = test_lke_cluster_acl

    acl = (
        exec_test_command(
            BASE_CMD
            + [
                "cluster-acl-view",
                cluster_id,
                "--text",
            ]
        )
        .stdout.decode()
        .strip()
    )

    headers = [
        "acl.enabled",
        "acl.addresses.ipv4",
        "acl.addresses.ipv6",
        "acl.revision-id",
    ]

    assert_headers_in_lines(headers, acl.splitlines())

    assert "True" in acl


def test_cluster_acl_update(test_lke_cluster_acl):
    cluster_id = test_lke_cluster_acl

    print("RUNNING TEST")

    # Verify the update
    acl = (
        exec_test_command(
            BASE_CMD
            + [
                "cluster-acl-update",
                cluster_id,
                "--acl.addresses.ipv4",
                "203.0.113.1",
                "--acl.addresses.ipv6",
                "2001:db8:1234:abcd::/64",
                "--acl.enabled",
                "true",
                "--text",
            ]
        )
        .stdout.decode()
        .strip()
    )

    headers = [
        "acl.enabled",
        "acl.addresses.ipv4",
        "acl.addresses.ipv6",
        "acl.revision-id",
    ]

    assert_headers_in_lines(headers, acl.splitlines())

    assert "203.0.113.1" in acl
    assert "2001:db8:1234:abcd::/64" in acl


def test_cluster_acl_delete(test_lke_cluster_acl):
    cluster_id = test_lke_cluster_acl

    retry_exec_test_command_with_delay(
        BASE_CMD + ["cluster-acl-delete", cluster_id]
    )

    # Verify the deletion
    acl = (
        exec_test_command(
            BASE_CMD
            + [
                "cluster-acl-view",
                cluster_id,
                "--text",
                "--format=acl.enabled",
                "--text",
            ]
        )
        .stdout.decode()
        .strip()
    )

    assert "False" in acl
