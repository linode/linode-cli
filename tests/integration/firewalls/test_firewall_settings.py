import json

import pytest

from tests.integration.helpers import (
    exec_test_command,
)

BASE_CMD = ["linode-cli", "firewalls"]


def test_firewall_settings_defaults(test_firewall_id, test_firewall_label):
    # list all firewalls and extract the IDs
    list_result = (
        exec_test_command(
            BASE_CMD + ["list", "--no-headers", "--text", "--delimiter", ","]
        )
        .stdout.decode()
        .strip()
    )

    firewall_lines = list_result.splitlines()
    firewall_ids = [
        line.split(",")[0].strip() for line in firewall_lines if line
    ]

    assert (
        test_firewall_id in firewall_ids
    ), f"{test_firewall_id} not found in firewall list"

    # get the default firewall settings
    settings_result = exec_test_command(
        BASE_CMD + ["firewall-settings-list", "--json"]
    ).stdout.decode()

    settings = json.loads(settings_result)
    assert (
        isinstance(settings, list) and len(settings) > 0
    ), "Unexpected settings format"

    default_ids = settings[0]["default_firewall_ids"]

    # Validate all expected keys exist and map to a valid firewall ID
    expected_keys = [
        "linode",
        "nodebalancer",
        "public_interface",
        "vpc_interface",
    ]

    for key in expected_keys:
        assert key in default_ids, f"Missing default_firewall_ids key: {key}"
        val = default_ids[key]
        assert val is None or isinstance(
            val, int
        ), f"{key} value is not None or int: {val}"
        if isinstance(val, int):
            assert val > 0, f"{key} should be a non-zero firewall ID"
            assert (
                str(val) in firewall_ids
            ), f"{key} ID ({val}) not found in firewall list"


def test_update_firewall_defaults(test_firewall_id, restore_firewall_defaults):
    # Fetch current default firewall settings
    settings = json.loads(
        exec_test_command(
            BASE_CMD + ["firewall-settings-list", "--json"]
        ).stdout.decode()
    )
    default_ids_before = settings[0]["default_firewall_ids"]

    # Skip if no default firewall configured at all
    if all(v is None for v in default_ids_before.values()):
        pytest.skip("Skipping: no default firewall configured for the account.")

    old_default_id = (
        str(default_ids_before["linode"])
        if default_ids_before["linode"]
        else None
    )

    # List all firewalls
    firewall_list = (
        exec_test_command(
            BASE_CMD + ["list", "--no-headers", "--text", "--delimiter", ","]
        )
        .stdout.decode()
        .strip()
    )

    firewall_ids = [
        line.split(",")[0].strip()
        for line in firewall_list.splitlines()
        if line
    ]

    assert (
        test_firewall_id in firewall_ids
    ), f"{test_firewall_id} not found in firewall list"

    new_id = next(
        fid
        for fid in firewall_ids
        if old_default_id is None or fid != old_default_id
    )

    # Update all default firewall IDs to the new one
    exec_test_command(
        BASE_CMD
        + [
            "firewall-settings-update",
            "--default_firewall_ids.linode",
            new_id,
            "--default_firewall_ids.nodebalancer",
            new_id,
            "--default_firewall_ids.public_interface",
            new_id,
            "--default_firewall_ids.vpc_interface",
            new_id,
            "--json",
        ]
    )

    # Verify update
    updated_settings = json.loads(
        exec_test_command(
            BASE_CMD + ["firewall-settings-list", "--json"]
        ).stdout.decode()
    )[0]["default_firewall_ids"]

    for key, val in updated_settings.items():
        assert (
            str(val) == new_id
        ), f"{key} was not updated (expected {new_id}, got {val})"
