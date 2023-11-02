import re
import time

import pytest

from tests.integration.helpers import (
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "firewalls"]
FIREWALL_LABEL = "label-fw-test" + str(int(time.time()))


@pytest.fixture
def test_firewall_id():
    # Create one domain for some tests in this suite
    firewall_id = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                FIREWALL_LABEL,
                "--rules.outbound_policy",
                "ACCEPT",
                "--rules.inbound_policy",
                "DROP",
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield firewall_id
    # teardown - delete all firewalls
    delete_target_id(target="firewalls", id=firewall_id)


@pytest.mark.smoke
def test_view_firewall(test_firewall_id):
    firewall_id = test_firewall_id

    result = (
        exec_test_command(
            BASE_CMD
            + [
                "view",
                firewall_id,
                "--no-headers",
                "--text",
                "--delimiter",
                ",",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search(firewall_id + "," + FIREWALL_LABEL + ",enabled", result)


def test_list_firewall(test_firewall_id):
    firewall_id = test_firewall_id

    result = (
        exec_test_command(
            BASE_CMD + ["list", "--no-headers", "--text", "--delimiter", ","]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search(firewall_id + "," + FIREWALL_LABEL + ",enabled", result)


@pytest.mark.smoke
def test_create_firewall_with_minimum_required_args():
    timestamp = str(time.time_ns())
    firewall_label = "label-fw-test" + timestamp
    result = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                firewall_label,
                "--rules.outbound_policy",
                "ACCEPT",
                "--rules.inbound_policy",
                "DROP",
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search("[0-9]+," + firewall_label + ",enabled", result)

    res_arr = result.split(",")
    firewall_id = res_arr[0]
    delete_target_id(target="firewalls", id=firewall_id)


def test_fails_to_create_firewall_without_inbound_policy():
    timestamp = str(time.time_ns())
    firewall_label = "fw_label" + timestamp
    result = (
        exec_failing_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                firewall_label,
                "--rules.outbound_policy",
                "ACCEPT",
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stderr.decode()
        .rstrip()
    )

    assert "inbound_policy is required" in result


def test_fails_to_create_firewall_without_outbound_policy():
    timestamp = str(time.time_ns())
    firewall_label = "fw_label" + timestamp
    result = (
        exec_failing_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                firewall_label,
                "--rules.inbound_policy",
                "DROP",
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stderr.decode()
        .rstrip()
    )

    assert "outbound_policy is required" in result


def test_firewall_label_must_be_unique_upon_creation(test_firewall_id):
    result = (
        exec_failing_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                FIREWALL_LABEL,
                "--rules.outbound_policy",
                "ACCEPT",
                "--rules.inbound_policy",
                "DROP",
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stderr.decode()
        .rstrip()
    )

    assert "Label must be unique among your Cloud Firewalls" in result


def test_create_firewall_with_inbound_and_outbound_args():
    timestamp = str(time.time_ns())
    firewall_label = "label-fw-test" + timestamp
    result = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                firewall_label,
                "--rules.outbound_policy",
                "ACCEPT",
                "--rules.inbound_policy",
                "DROP",
                "--rules.inbound",
                '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.2/32"]}, "action": "ACCEPT", "label": "accept-inbound-SSH"}]',
                "--rules.outbound",
                '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": "accept-outbound-SSH"}]',
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search("[0-9]+," + firewall_label + ",enabled", result)

    res_arr = result.split(",")
    firewall_id = res_arr[0]
    delete_target_id(target="firewalls", id=firewall_id)


def test_update_firewall(test_firewall_id):
    timestamp = str(time.time_ns())
    firewall_id = test_firewall_id
    updated_tag = "updated-tag" + timestamp
    updated_label = "updated-" + timestamp

    result = (
        exec_test_command(
            BASE_CMD
            + [
                "update",
                firewall_id,
                "--tags",
                updated_tag,
                "--label",
                updated_label,
                "--status",
                "enabled",
                "--no-headers",
                "--text",
                "--delimiter",
                ",",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search(firewall_id + "," + updated_label + ",enabled", result)
