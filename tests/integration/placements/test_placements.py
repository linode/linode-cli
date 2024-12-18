import time

import pytest

from tests.integration.helpers import (
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "placement"]


@pytest.fixture(scope="module")
def create_placement_group():
    new_label = str(time.time_ns()) + "label"
    placement_group_id = (
        exec_test_command(
            BASE_CMD
            + [
                "group-create",
                "--label",
                new_label,
                "--region",
                "us-mia",
                "--placement_group_type",
                "anti_affinity:local",
                "--placement_group_policy",
                "strict",
                "--text",
                "--no-headers",
                "--format=id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    yield placement_group_id
    delete_target_id(
        target="placement", delete_command="group-delete", id=placement_group_id
    )


def test_placement_group_list():
    res = (
        exec_test_command(BASE_CMD + ["groups-list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["placement_group_type", "region", "label"]
    assert_headers_in_lines(headers, lines)


def test_placement_group_view(create_placement_group):
    placement_group_id = create_placement_group
    res = (
        exec_test_command(
            BASE_CMD
            + ["group-view", placement_group_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["placement_group_type", "region", "label"]
    assert_headers_in_lines(headers, lines)


def test_assign_placement_group(support_test_linode_id, create_placement_group):
    linode_id = support_test_linode_id
    placement_group_id = create_placement_group
    process = exec_test_command(
        BASE_CMD
        + [
            "assign-linode",
            placement_group_id,
            "--linode",
            linode_id,
            "--text",
            "--delimiter=,",
        ]
    )
    assert process.returncode == 0


def test_unassign_placement_group(
    support_test_linode_id, create_placement_group
):
    linode_id = support_test_linode_id
    placement_group_id = create_placement_group
    process = exec_test_command(
        BASE_CMD
        + [
            "unassign-linode",
            placement_group_id,
            "--linode",
            linode_id,
            "--text",
            "--delimiter=,",
        ]
    )
    assert process.returncode == 0


def test_update_placement_group(create_placement_group):
    placement_group_id = create_placement_group
    new_label = str(time.time_ns()) + "label"
    updated_label = (
        exec_test_command(
            BASE_CMD
            + [
                "group-update",
                placement_group_id,
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
