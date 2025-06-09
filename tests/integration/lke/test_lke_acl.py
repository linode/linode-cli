from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_test_command,
    retry_exec_test_command_with_delay,
)
from tests.integration.lke.fixtures import lke_cluster_acl  # noqa: #401


def test_cluster_acl_view(lke_cluster_acl):
    cluster_id = lke_cluster_acl

    acl = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "cluster-acl-view",
            cluster_id,
            "--text",
        ]
    )

    headers = [
        "acl.enabled",
        "acl.addresses.ipv4",
        "acl.addresses.ipv6",
        "acl.revision-id",
    ]

    assert_headers_in_lines(headers, acl.splitlines())

    assert "True" in acl


def test_cluster_acl_update(lke_cluster_acl):
    cluster_id = lke_cluster_acl

    print("RUNNING TEST")

    # Verify the update
    acl = exec_test_command(
        BASE_CMDS["lke"]
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

    headers = [
        "acl.enabled",
        "acl.addresses.ipv4",
        "acl.addresses.ipv6",
        "acl.revision-id",
    ]

    assert_headers_in_lines(headers, acl.splitlines())

    assert "203.0.113.1" in acl
    assert "2001:db8:1234:abcd::/64" in acl


def test_cluster_acl_delete(lke_cluster_acl):
    cluster_id = lke_cluster_acl

    retry_exec_test_command_with_delay(
        BASE_CMDS["lke"] + ["cluster-acl-delete", cluster_id]
    )

    # Verify the deletion
    acl = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "cluster-acl-view",
            cluster_id,
            "--text",
            "--format=acl.enabled",
            "--text",
        ]
    )

    assert "False" in acl
