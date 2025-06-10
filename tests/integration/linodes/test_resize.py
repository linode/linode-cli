import os

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    exec_failing_test_command,
    exec_test_command,
)
from tests.integration.linodes.fixtures import (  # noqa: F401
    linode_instance_for_resize_tests,
)
from tests.integration.linodes.helpers import (
    wait_until,
)


@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_resize_fails_to_the_same_plan(linode_instance_for_resize_tests):
    linode_id = linode_instance_for_resize_tests
    linode_plan = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "view",
            linode_id,
            "--format",
            "type",
            "--text",
            "--no-headers",
        ]
    )

    result = exec_failing_test_command(
        BASE_CMDS["linodes"]
        + [
            "resize",
            "--type",
            linode_plan,
            "--text",
            "--no-headers",
            linode_id,
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 400" in result
    assert "Linode is already running this service plan." in result


def test_resize_fails_to_smaller_plan(linode_instance_for_resize_tests):
    linode_id = linode_instance_for_resize_tests
    smaller_plan = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "types",
            "--format",
            "id",
            "--text",
            "--no-headers",
        ]
    ).splitlines()[0]

    result = exec_failing_test_command(
        BASE_CMDS["linodes"]
        + [
            "resize",
            "--type",
            smaller_plan,
            "--text",
            "--no-headers",
            linode_id,
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 400" in result
    assert (
        "Linode has allocated more disk than the new service plan allows. Delete or resize disks smaller."
        in result
    )


def test_resize_fail_to_invalid_plan(linode_instance_for_resize_tests):
    invalid_plan = "g15-bad-plan"
    linode_id = linode_instance_for_resize_tests

    result = exec_failing_test_command(
        BASE_CMDS["linodes"]
        + [
            "resize",
            "--type",
            invalid_plan,
            "--text",
            "--no-headers",
            linode_id,
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 400" in result
    assert "type	A valid plan type by that ID was not found" in result


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "True",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=True",
)
def test_resize_to_next_size_plan(linode_instance_for_resize_tests):
    linode_id = linode_instance_for_resize_tests
    larger_plan = exec_test_command(
        BASE_CMDS["linodes"][
            "types",
            "--format",
            "id",
            "--text",
            "--no-headers",
        ]
    ).splitlines()[2]

    exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "resize",
            "--allow_auto_disk_resize=true",
            "--type",
            larger_plan,
            "--text",
            "--no-headers",
            linode_id,
        ]
    )

    # check resize status
    assert wait_until(
        linode_id=linode_id, timeout=180, status="resizing"
    ), "linode failed to change status to resizing.."

    # Wait for offline status.
    # Linodes that are resized do not boot automatically
    assert wait_until(
        linode_id=linode_id, timeout=180, status="offline", period=15
    ), "linode failed to change status to resizing.."

    result = exec_test_command(
        BASE_CMDS["linodes"]
        + ["view", linode_id, "--format", "type", "--text", "--no-headers"]
    )

    assert larger_plan in result
