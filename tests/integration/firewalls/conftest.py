import json

import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    check_attribute_value,
    delete_target_id,
    exec_test_command,
    get_random_text,
    wait_for_condition,
)


def get_firewall_defaults():
    result = json.loads(
        exec_test_command(
            BASE_CMDS["firewalls"]
            + [
                "firewall-settings-list",
                "--json",
            ],
        )
    )[0]["default_firewall_ids"]

    return result


@pytest.fixture(scope="function")
def _firewall_id_and_label():
    label = "test-fw-" + get_random_text(5)
    firewall_id = exec_test_command(
        BASE_CMDS["firewalls"]
        + [
            "create",
            "--label",
            label,
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

    # Verify firewall status is reachable before proceeding with tests
    wait_for_condition(
        5,
        60,
        check_attribute_value,
        "firewalls",
        "view",
        firewall_id,
        "status",
        "enabled",
    )

    yield firewall_id, label

    # cleanup (possible for non-default firewalls only)
    delete_target_id(target="firewalls", id=firewall_id)


@pytest.fixture(scope="function")
def get_firewall_id(_firewall_id_and_label):
    """Only the ID, so old tests keep working."""
    return _firewall_id_and_label[0]


@pytest.fixture(scope="function")
def get_firewall_label(_firewall_id_and_label):
    """Only the label, for tests that need it explicitly."""
    return _firewall_id_and_label[1]


@pytest.fixture
def restore_firewall_defaults():
    # Fetch and store current default firewall settings
    original_defaults = get_firewall_defaults()

    yield original_defaults

    # Restore the original defaults after test
    args = []
    for key, val in original_defaults.items():
        if val is not None:
            args.extend([f"--default_firewall_ids.{key}", str(val)])

    if args:
        exec_test_command(
            BASE_CMDS["firewalls"] + ["firewall-settings-update"] + args
        )
