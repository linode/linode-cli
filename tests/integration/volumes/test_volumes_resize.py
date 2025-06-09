import os
import time

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    exec_failing_test_command,
    exec_test_command,
)
from tests.integration.volumes.fixtures import volume_instance_id  # noqa: #401


def test_resize_fails_to_smaller_volume(volume_instance_id):
    volume_id = volume_instance_id
    time.sleep(5)
    result = exec_failing_test_command(
        BASE_CMDS["volumes"]
        + ["resize", volume_id, "--size", "5", "--text", "--no-headers"],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 400" in result
    assert "Storage volumes can only be resized up" in result


def test_resize_fails_to_volume_larger_than_1024gb(volume_instance_id):
    volume_id = volume_instance_id
    result = exec_failing_test_command(
        BASE_CMDS["volumes"]
        + [
            "resize",
            volume_id,
            "--size",
            "1024893405",
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    )

    if "test" == os.environ.get(
        "TEST_ENVIRONMENT", None
    ) or "dev" == os.environ.get("TEST_ENVIRONMENT", None):
        assert (
            "Storage volumes cannot be resized larger than 1024 gigabytes"
            in result
        )
    else:
        assert (
            "Storage volumes cannot be resized larger than 16384 gigabytes"
            in result
        )


def test_resize_volume(volume_instance_id):
    volume_id = volume_instance_id

    exec_test_command(
        BASE_CMDS["volumes"]
        + ["resize", volume_id, "--size", "11", "--text", "--no-headers"]
    )

    result = exec_test_command(
        BASE_CMDS["volumes"]
        + ["view", volume_id, "--format", "size", "--text", "--no-headers"]
    )

    assert "11" in result
