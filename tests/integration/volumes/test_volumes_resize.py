import time

import pytest

from tests.integration.helpers import (
    exec_failing_test_command,
    exec_test_command,
    os,
    remove_all,
)

BASE_CMD = ["linode-cli", "volumes"]
timestamp = str(int(time.time()))
VOLUME_CREATION_WAIT = 5


@pytest.fixture(scope="session", autouse=True)
def setup_test_volumes_resize():
    remove_all(target="volumes")
    volume_id = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                "A" + timestamp,
                "--region",
                "us-east",
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
    remove_all(target="volumes")


def test_resize_fails_to_smaller_volume(setup_test_volumes_resize):
    volume_id = setup_test_volumes_resize
    time.sleep(VOLUME_CREATION_WAIT)
    result = exec_failing_test_command(
        BASE_CMD
        + ["resize", volume_id, "--size", "5", "--text", "--no-headers"]
    ).stderr.decode()

    assert "Request failed: 400" in result
    assert "Storage volumes can only be resized up" in result


def test_resize_fails_to_volume_larger_than_1024gb(setup_test_volumes_resize):
    volume_id = setup_test_volumes_resize
    result = exec_failing_test_command(
        BASE_CMD
        + [
            "resize",
            volume_id,
            "--size",
            "1024893405",
            "--text",
            "--no-headers",
        ]
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


def test_resize_volume(setup_test_volumes_resize):
    volume_id = setup_test_volumes_resize

    exec_test_command(
        BASE_CMD
        + ["resize", volume_id, "--size", "11", "--text", "--no-headers"]
    )

    result = exec_test_command(
        BASE_CMD
        + ["view", volume_id, "--format", "size", "--text", "--no-headers"]
    ).stdout.decode()

    assert "11" in result
