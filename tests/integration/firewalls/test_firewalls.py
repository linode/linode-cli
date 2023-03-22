import logging
import re
import time

import pytest

from tests.integration.helpers import (
    exec_failing_test_command,
    exec_test_command,
    remove_all,
)

BASE_CMD = ["linode-cli", "firewalls"]
FIREWALL_LABEL = "example-firewall-label"


@pytest.fixture(scope="session", autouse=True)
def firewalls_setup():
    # Create one domain for some tests in this suite
    try:
        # Create domain
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
    except:
        logging.exception("Failed creating domain in setup")

    yield firewall_id
    # teardown - delete all firewalls
    try:
        remove_all(target="firewalls")
    except:
        logging.exception("Failed to delete all firewalls")


def test_view_firewall(firewalls_setup):
    firewall_id = firewalls_setup

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


def test_list_firewall(firewalls_setup):
    firewall_id = firewalls_setup

    result = (
        exec_test_command(
            BASE_CMD + ["list", "--no-headers", "--text", "--delimiter", ","]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search(firewall_id + "," + FIREWALL_LABEL + ",enabled", result)


def test_create_firewall_with_minimum_required_args():
    timestamp = str(int(time.time()))
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


def test_fails_to_create_firewall_without_inbound_policy():
    result = (
        exec_failing_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                FIREWALL_LABEL,
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
    result = (
        exec_failing_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                FIREWALL_LABEL,
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


def test_firewall_label_must_be_unique_upon_creation(firewalls_setup):
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
    timestamp = str(int(time.time()))
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


def test_update_firewall(firewalls_setup):
    firewall_id = firewalls_setup
    updated_tag = "updated-tag"
    updated_label = "updated-label"

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
