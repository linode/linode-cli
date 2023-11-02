import os
import re

import pytest

from tests.integration.helpers import delete_target_id, exec_test_command
from tests.integration.linodes.helpers_linodes import (
    BASE_CMD,
    create_linode,
    create_linode_and_wait,
)

# ##################################################################
# #  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
# #  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
# ##################################################################
snapshot_label = "test_snapshot1"


@pytest.fixture
def create_linode_setup():
    linode_id = create_linode()

    yield linode_id

    delete_target_id("linodes", linode_id)


def test_create_linode_with_backup_disabled(create_linode_setup):
    linode_id = create_linode_setup
    result = exec_test_command(
        BASE_CMD
        + [
            "list",
            "--format=id,enabled",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    ).stdout.decode()

    assert re.search(linode_id + ",False", result)


@pytest.mark.smoke
def test_enable_backups(create_linode_setup):
    # get linode id
    linode_id = create_linode_setup

    # enable backup
    exec_test_command(
        BASE_CMD + ["backups-enable", linode_id, "--text", "--no-headers"]
    )

    result = exec_test_command(
        BASE_CMD
        + [
            "list",
            "--format=id,enabled",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    ).stdout.decode()

    assert re.search(linode_id + ",True", result)


def test_create_backup_with_backup_enabled(linode_backup_enabled):
    linode_id = linode_backup_enabled
    result = exec_test_command(
        BASE_CMD
        + [
            "list",
            "--format=id,enabled",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    ).stdout.decode()

    assert re.search(linode_id + ",True", result)


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "TRUE",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE",
)
def test_take_snapshot_of_linode():
    # get linode id after creation and wait for "running" status
    linode_id = create_linode_and_wait()

    result = exec_test_command(
        BASE_CMD
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
    ).stdout.decode()
    assert re.search(
        "[0-9]+,pending,snapshot,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,"
        + snapshot_label,
        result,
    )


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "TRUE",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE",
)
def test_view_the_snapshot(snapshot_of_linode):
    # get linode id after creation and wait for "running" status
    linode_id = snapshot_of_linode[0]
    new_snapshot_label = snapshot_of_linode[1]

    result = exec_test_command(
        BASE_CMD
        + [
            "backups-list",
            linode_id,
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    ).stdout.decode()

    assert re.search(
        "[0-9]+,pending,snapshot,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,"
        + new_snapshot_label,
        result,
    )


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "TRUE",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE",
)
def test_cancel_backups(snapshot_of_linode):
    # get linode id after creation and wait for "running" status
    linode_id = snapshot_of_linode[0]
    new_snapshot_label = snapshot_of_linode[1]

    result = exec_test_command(
        BASE_CMD
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
    ).stdout.decode()
    assert re.search(
        "[0-9]+,pending,snapshot,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,"
        + new_snapshot_label,
        result,
    )

    # cancel snapshot
    exec_test_command(
        BASE_CMD + ["backups-cancel", linode_id, "--text", "--no-headers"]
    )
