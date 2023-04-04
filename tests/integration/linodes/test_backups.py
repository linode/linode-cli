import logging
import os
import re

import pytest

from tests.integration.helpers import delete_target_id, exec_test_command
from tests.integration.linodes.helpers_linodes import (
    BASE_CMD,
    DEFAULT_RANDOM_PASS,
    DEFAULT_REGION,
    DEFAULT_TEST_IMAGE,
    create_linode,
    create_linode_and_wait,
)

# ##################################################################
# #  WARNING: THIS TEST WILL DELETE ALL OF YOUR LINODES            #
# #  WARNING: USE A SEPARATE TEST ACCOUNT WHEN RUNNING THESE TESTS #
# ##################################################################
snapshot_label = "test_snapshot1"


@pytest.fixture(scope="session", autouse=True)
def setup_backup():
    # skip all test if TEST_ENVIRONMENT variable is "test" or "dev"
    if "test" == os.environ.get(
        "TEST_ENVIRONMENT", None
    ) or "dev" == os.environ.get("TEST_ENVIRONMENT", None):
        pytest.skip(allow_module_level=True)
    else:
        # create linode with back up disabled
        linode_id = create_linode()
    yield linode_id
    # teadown clean up (delete all linodes)
    try:
        delete_target_id(target="linodes", id=linode_id)
    except:
        logging.exception("Fail to remove linode..")


def test_create_linode_with_backup_disabled():
    new_linode_id = create_linode()
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

    assert re.search(new_linode_id + ",False", result)
    delete_target_id(target="linodes", id=new_linode_id)


def test_enable_backups(setup_backup):
    # get linode id
    linode_id = setup_backup

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


def test_create_backup_with_backup_enabled():
    linode_type = (
        os.popen(
            "linode-cli linodes types --text --no-headers --format='id' | xargs | awk '{ print $1 }'"
        )
        .read()
        .rstrip()
    )

    # create linode with backups enabled
    linode_id = (
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "create",
                "--backups_enabled",
                "true",
                "--type",
                linode_type,
                "--region",
                DEFAULT_REGION,
                "--image",
                DEFAULT_TEST_IMAGE,
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--text",
                "--no-headers",
                "--format=id",
            ]
        )
        .stdout.decode()
        .rstrip()
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

    delete_target_id(target="linodes", id=linode_id)


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

    delete_target_id(target="linodes", id=linode_id)


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "TRUE",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE",
)
def test_view_the_snapshot():
    # get linode id after creation and wait for "running" status
    linode_id = create_linode_and_wait()
    new_snapshot_label = "test_snapshot2"

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

    delete_target_id(target="linodes", id=linode_id)

    # BUG outputs the backup as json, assertion below asserts that outputs the expected.
    # assert(re.search("'status':.*'pending", result))
    # assert(re.search("'finished':.*None", result))
    # assert(re.search("'type':.*'snapshot'", result))
    # assert(re.search("'label':.*"+new_snapshot_label, result))
    # assert(re.search("'region':.*'us-east'", result))
    # assert(re.search("'id':.*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]", result))


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "TRUE",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE",
)
def test_cancel_backups():
    # get linode id after creation and wait for "running" status
    linode_id = create_linode_and_wait()
    new_snapshot_label = "test_snapshot3"

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

    delete_target_id(target="linodes", id=linode_id)
