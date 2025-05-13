import re

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.firewalls.fixtures import (  # noqa: F401
    FIREWALL_LABEL,
    firewall_id,
)
from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
)


@pytest.mark.smoke
def test_view_firewall(firewall_id):
    firewall_id = firewall_id

    result = exec_test_command(
        BASE_CMDS["firewalls"]
        + [
            "view",
            firewall_id,
            "--no-headers",
            "--text",
            "--delimiter",
            ",",
        ]
    )

    assert re.search(firewall_id + "," + FIREWALL_LABEL + ",enabled", result)


def test_list_firewall(firewall_id):
    firewall_id = firewall_id

    result = exec_test_command(
        BASE_CMDS["firewalls"]
        + ["list", "--no-headers", "--text", "--delimiter", ","]
    )

    assert re.search(firewall_id + "," + FIREWALL_LABEL + ",enabled", result)


@pytest.mark.smoke
def test_create_firewall_with_minimum_required_args():
    firewall_label = "label-fw-test" + get_random_text(5)
    result = exec_test_command(
        BASE_CMDS["firewalls"]
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

    assert re.search("[0-9]+," + firewall_label + ",enabled", result)

    res_arr = result.split(",")
    firewall_id = res_arr[0]
    delete_target_id(target="firewalls", id=firewall_id)


def test_fails_to_create_firewall_without_inbound_policy():
    firewall_label = "fw_label" + get_random_text(5)
    result = exec_failing_test_command(
        BASE_CMDS["firewalls"]
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
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "inbound_policy is required" in result


def test_fails_to_create_firewall_without_outbound_policy():
    firewall_label = "fw_label" + get_random_text(5)
    result = exec_failing_test_command(
        BASE_CMDS["firewalls"]
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
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "outbound_policy is required" in result


def test_firewall_label_must_be_unique_upon_creation(firewall_id):
    result = exec_failing_test_command(
        BASE_CMDS["firewalls"]
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
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Label must be unique among your Cloud Firewalls" in result


def test_create_firewall_with_inbound_and_outbound_args():
    firewall_label = "label-fw-test" + get_random_text(5)
    result = exec_test_command(
        BASE_CMDS["firewalls"]
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

    assert re.search("[0-9]+," + firewall_label + ",enabled", result)

    res_arr = result.split(",")
    firewall_id = res_arr[0]
    delete_target_id(target="firewalls", id=firewall_id)


def test_update_firewall(firewall_id):
    firewall_id = firewall_id
    updated_tag = "updated-tag" + get_random_text(5)
    updated_label = "updated-" + get_random_text(5)

    result = exec_test_command(
        BASE_CMDS["firewalls"]
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

    assert re.search(firewall_id + "," + updated_label + ",enabled", result)
