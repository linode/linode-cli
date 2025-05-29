import json

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    delete_target_id,
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
        assert isinstance(val, int), f"{key} value is not an integer"
        assert val > 0, f"{key} should be a non-zero firewall ID"
        assert (
            str(val) in firewall_ids
        ), f"{key} ID ({val}) not found in firewall list"


@pytest.mark.skip("skip until there is a way to delete default firewall")
def test_update_firewall_defaults(test_firewall_id):
    # fetch current default firewall IDs
    settings_result = exec_test_command(
        BASE_CMD + ["firewall-settings-list", "--json"]
    ).stdout.decode()
    settings = json.loads(settings_result)
    default_ids_before = settings[0]["default_firewall_ids"]

    # remember the old default so we can delete it later
    old_default_id = str(default_ids_before["linode"])

    # list all firewall IDs
    list_result = (
        exec_test_command(
            BASE_CMD + ["list", "--no-headers", "--text", "--delimiter", ","]
        )
        .stdout.decode()
        .strip()
    )
    firewall_ids = [
        line.split(",")[0].strip() for line in list_result.splitlines() if line
    ]

    assert (
        test_firewall_id in firewall_ids
    ), f"{test_firewall_id} not found in firewall list"

    # pick a new ID different from the old default
    new_id = next(fid for fid in firewall_ids if fid != old_default_id)

    # update all defaults to the new one
    result = exec_test_command(
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
    assert result.returncode == ExitCodes.SUCCESS, result.stderr.decode()

    # fetch settings again and verify the update
    settings_after = json.loads(
        exec_test_command(
            BASE_CMD + ["firewall-settings-list", "--json"]
        ).stdout.decode()
    )[0]["default_firewall_ids"]

    for key, val in settings_after.items():
        assert (
            str(val) == new_id
        ), f"{key} was not updated (expected {new_id}, got {val})"

    # delete the old default firewall resource
    delete_target_id(target="firewalls", id=old_default_id)
