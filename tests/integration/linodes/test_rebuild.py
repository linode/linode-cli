import os

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    exec_failing_test_command,
    exec_test_command,
    retry_exec_test_command_with_delay,
)
from tests.integration.linodes.fixtures import (  # noqa: #401
    linode_for_rebuild_tests,
)
from tests.integration.linodes.helpers import (
    DEFAULT_RANDOM_PASS,
    wait_until,
)


@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_rebuild_fails_without_image(linode_for_rebuild_tests):
    result = exec_failing_test_command(
        BASE_CMDS["linodes"]
        + [
            "rebuild",
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            linode_for_rebuild_tests,
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 400" in result
    assert "You must specify an image" in result


def test_rebuild_fails_with_invalid_image(linode_for_rebuild_tests):
    linode_id = linode_for_rebuild_tests
    rebuild_image = "bad/image"

    result = exec_failing_test_command(
        BASE_CMDS["linodes"]
        + [
            "rebuild",
            "--image",
            rebuild_image,
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            linode_id,
            "--text",
            "--no-headers",
        ]
    )

    assert "Request failed: 400" in result


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "True",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=True",
)
@pytest.mark.flaky(reruns=3, reruns_delay=5)
def test_rebuild_a_linode(linode_for_rebuild_tests):
    linode_id = linode_for_rebuild_tests
    rebuild_image = "linode/alpine3.20"

    # trigger rebuild
    exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "rebuild",
            "--image",
            rebuild_image,
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            "--text",
            "--no-headers",
            linode_id,
        ]
    )

    # check status for rebuilding
    assert wait_until(
        linode_id=linode_id, timeout=180, status="rebuilding"
    ), "linode failed to change status to rebuilding.."

    # check if rebuilding finished
    assert wait_until(
        linode_id=linode_id, timeout=180, status="running"
    ), "linode failed to change status to running from rebuilding.."

    result = exec_test_command(
        BASE_CMDS["linodes"]
        + ["view", linode_id, "--format", "image", "--text", "--no-headers"]
    ).stdout.decode()
    assert rebuild_image in result


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "True",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=True",
)
@pytest.mark.flaky(reruns=3, reruns_delay=5)
def test_rebuild_linode_disk_encryption_enabled(linode_for_rebuild_tests):
    linode_id = linode_for_rebuild_tests
    rebuild_image = "linode/alpine3.20"

    # trigger rebuild
    retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"]
        + [
            "rebuild",
            linode_id,
            "--image",
            rebuild_image,
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            "--text",
            "--no-headers",
            "--disk_encryption",
            "enabled",
        ],
        retries=3,
        delay=10,
    )

    # check status for rebuilding
    assert wait_until(
        linode_id=linode_id, timeout=180, status="rebuilding"
    ), "linode failed to change status to rebuilding.."

    # check if rebuilding finished
    assert wait_until(
        linode_id=linode_id, timeout=180, status="running"
    ), "linode failed to change status to running from rebuilding.."

    result = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "view",
            linode_id,
            "--format",
            "image",
            "--text",
            "--no-headers",
            "--format=id,image,disk_encryption",
        ]
    )

    assert "enabled" in result
    assert rebuild_image in result


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "True",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=True",
)
@pytest.mark.flaky(reruns=3, reruns_delay=5)
def test_rebuild_linode_disk_encryption_disabled(linode_for_rebuild_tests):
    linode_id = linode_for_rebuild_tests
    rebuild_image = "linode/alpine3.20"

    # trigger rebuild
    retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"]
        + [
            "rebuild",
            linode_id,
            "--image",
            rebuild_image,
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            "--text",
            "--no-headers",
            "--disk_encryption",
            "disabled",
        ],
        retries=3,
        delay=10,
    )

    # check status for rebuilding
    assert wait_until(
        linode_id=linode_id, timeout=180, status="rebuilding"
    ), "linode failed to change status to rebuilding.."

    # check if rebuilding finished
    assert wait_until(
        linode_id=linode_id, timeout=180, status="running"
    ), "linode failed to change status to running from rebuilding.."

    result = retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"]
        + [
            "view",
            linode_id,
            "--format",
            "image",
            "--text",
            "--no-headers",
            "--format=id,image,disk_encryption",
        ],
        retries=3,
        delay=10,
    )

    assert "disabled" in result
    assert rebuild_image in result
