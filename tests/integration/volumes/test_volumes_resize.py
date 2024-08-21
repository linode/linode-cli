import os
import time

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "volumes"]
timestamp = str(time.time_ns())
VOLUME_CREATION_WAIT = 5


@pytest.fixture(scope="package")
def test_volume_id():
    volume_id = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                "A" + timestamp,
                "--region",
                "us-ord",
                "--size",
                "10",
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield volume_id

    delete_target_id(target="volumes", id=volume_id)


def test_resize_fails_to_smaller_volume(test_volume_id):
    volume_id = test_volume_id
    time.sleep(VOLUME_CREATION_WAIT)
    result = exec_failing_test_command(
        BASE_CMD
        + ["resize", volume_id, "--size", "5", "--text", "--no-headers"],
        ExitCodes.REQUEST_FAILED,
    ).stderr.decode()

    assert "Request failed: 400" in result
    assert "Storage volumes can only be resized up" in result


def test_resize_fails_to_volume_larger_than_1024gb(test_volume_id):
    volume_id = test_volume_id
    result = exec_failing_test_command(
        BASE_CMD
        + [
            "resize",
            volume_id,
            "--size",
            "1024893405",
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    ).stderr.decode()

    if "test" == os.environ.get(
        "TEST_ENVIRONMENT", None
    ) or "dev" == os.environ.get("TEST_ENVIRONMENT", None):
        assert (
            "Storage volumes cannot be resized larger than 1024 gigabytes"
            in result
        )
    else:
        assert (
            "Storage volumes cannot be resized larger than 10240 gigabytes"
            in result
        )


def test_resize_volume(test_volume_id):
    volume_id = test_volume_id

    exec_test_command(
        BASE_CMD
        + ["resize", volume_id, "--size", "11", "--text", "--no-headers"]
    )

    result = exec_test_command(
        BASE_CMD
        + ["view", volume_id, "--format", "size", "--text", "--no-headers"]
    ).stdout.decode()

    assert "11" in result
