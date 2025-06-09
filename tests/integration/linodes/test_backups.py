import os
import re

import pytest

from tests.integration.helpers import BASE_CMDS, exec_test_command
from tests.integration.linodes.fixtures import (  # noqa: F401
    linode_backup_disabled,
    linode_backup_enabled,
    linode_basic_with_firewall,
)
from tests.integration.linodes.helpers import (
    check_account_settings,
    create_linode_and_wait,
    set_backups_enabled_in_account_settings,
)


@pytest.mark.skipif(
    check_account_settings(), reason="Account is managed, skipping the test.."
)
def test_create_linode_with_backup_disabled(
    linode_backup_disabled,
):
    linode_id = linode_backup_disabled
    result = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "list",
            "--id",
            linode_id,
            "--format=id,backups.enabled",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    )

    assert re.search(linode_id + ",False", result)

    result = set_backups_enabled_in_account_settings(toggle=True)

    assert "True" in result


@pytest.mark.smoke
def test_enable_backups(linode_basic_with_firewall):
    # get linode id
    linode_id = linode_basic_with_firewall

    # enable backup
    exec_test_command(
        BASE_CMDS["linodes"]
        + ["backups-enable", linode_id, "--text", "--no-headers"]
    )

    result = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "list",
            "--format=id,backups.enabled",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    )

    assert re.search(linode_id + ",True", result)


def test_create_backup_with_backup_enabled(linode_backup_enabled):
    linode_id = linode_backup_enabled
    result = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "list",
            "--format=id,backups.enabled",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    )

    assert re.search(linode_id + ",True", result)


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "True",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=True",
)
def test_take_snapshot_of_linode():
    # get linode id after creation and wait for "running" status
    linode_id = create_linode_and_wait()

    snapshot_label = "test_snapshot1"

    result = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "snapshot",
            linode_id,
            "--label",
            snapshot_label,
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
        ]
    )
    assert re.search(
        "[0-9]+,pending,snapshot,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,"
        + snapshot_label,
        result,
    )


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "True",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=True",
)
def test_view_the_snapshot(snapshot_of_linode):
    # get linode id after creation and wait for "running" status
    linode_id = snapshot_of_linode[0]
    new_snapshot_label = snapshot_of_linode[1]

    result = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "backups-list",
            linode_id,
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    )

    assert re.search(
        "[0-9]+,pending,snapshot,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,"
        + new_snapshot_label,
        result,
    )


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "True",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=True",
)
def test_cancel_backups(snapshot_of_linode):
    # get linode id after creation and wait for "running" status
    linode_id = snapshot_of_linode[0]
    new_snapshot_label = snapshot_of_linode[1]

    result = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "snapshot",
            linode_id,
            "--label",
            new_snapshot_label,
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
        ]
    )
    assert re.search(
        "[0-9]+,pending,snapshot,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,"
        + new_snapshot_label,
        result,
    )

    # cancel snapshot
    exec_test_command(
        BASE_CMDS["linodes"]
        + ["backups-cancel", linode_id, "--text", "--no-headers"]
    )
