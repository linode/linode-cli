import os

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
)
from tests.integration.linodes.helpers_linodes import (
    BASE_CMD,
    create_linode_and_wait,
    wait_until,
)


@pytest.fixture(scope="session")
def test_linode_id(linode_cloud_firewall):
    plan = (
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "types",
                "--format",
                "id",
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()[1]
    )
    linode_id = create_linode_and_wait(
        firewall_id=linode_cloud_firewall, test_plan=plan
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_resize_fails_to_the_same_plan(test_linode_id):
    linode_id = test_linode_id
    linode_plan = (
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "view",
                linode_id,
                "--format",
                "type",
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    result = exec_failing_test_command(
        BASE_CMD
        + [
            "resize",
            "--type",
            linode_plan,
            "--text",
            "--no-headers",
            linode_id,
        ],
        ExitCodes.REQUEST_FAILED,
    ).stderr.decode()

    assert "Request failed: 400" in result
    assert "Linode is already running this service plan." in result


def test_resize_fails_to_smaller_plan(test_linode_id):
    linode_id = test_linode_id
    smaller_plan = (
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "types",
                "--format",
                "id",
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()[0]
    )

    result = exec_failing_test_command(
        BASE_CMD
        + [
            "resize",
            "--type",
            smaller_plan,
            "--text",
            "--no-headers",
            linode_id,
        ],
        ExitCodes.REQUEST_FAILED,
    ).stderr.decode()

    assert "Request failed: 400" in result
    assert (
        "Linode has allocated more disk than the new service plan allows. Delete or resize disks smaller."
        in result
    )


def test_resize_fail_to_invalid_plan(test_linode_id):
    invalid_plan = "g15-bad-plan"
    linode_id = test_linode_id

    result = exec_failing_test_command(
        BASE_CMD
        + [
            "resize",
            "--type",
            invalid_plan,
            "--text",
            "--no-headers",
            linode_id,
        ],
        ExitCodes.REQUEST_FAILED,
    ).stderr.decode()

    assert "Request failed: 400" in result
    assert "type	A valid plan type by that ID was not found" in result


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "True",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=True",
)
def test_resize_to_next_size_plan(test_linode_id):
    linode_id = test_linode_id
    larger_plan = (
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "types",
                "--format",
                "id",
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()[2]
    )

    exec_test_command(
        BASE_CMD
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
        BASE_CMD
        + ["view", linode_id, "--format", "type", "--text", "--no-headers"]
    ).stdout.decode()

    assert larger_plan in result
