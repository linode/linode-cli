import json

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_test_command,
    get_random_text,
    retry_exec_test_command_with_delay,
    wait_for_condition,
)
from tests.integration.linodes.fixtures import (  # noqa: F401
    linode_instance_disk_tests,
)
from tests.integration.linodes.helpers import (
    get_disk_ids,
)


def _get_smallest_disk_id(linode_id):
    """Return the disk ID of the smallest disk (e.g. swap) on the Linode."""
    disks_json = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "disks-list",
            linode_id,
            "--json",
        ]
    )
    disks = json.loads(disks_json)
    smallest = min(disks, key=lambda d: d["size"])
    return str(smallest["id"])


def test_disk_resize_clone_and_create(linode_instance_disk_tests):
    linode_id = linode_instance_disk_tests

    # Ensure disks are available
    def disks_ready():
        return len(get_disk_ids(linode_id=linode_id)) >= 2

    wait_for_condition(10, 120, disks_ready)

    # Use the smallest disk (swap) for resize/clone — the main OS disk
    # is too large to shrink to 50 MB because it contains filesystem data.
    disk_id = _get_smallest_disk_id(linode_id)

    def disk_poll_func():
        status = exec_test_command(
            BASE_CMDS["linodes"]
            + [
                "disk-view",
                linode_id,
                disk_id,
                "--text",
                "--no-headers",
                "--format=status",
            ]
        )

        return status.strip() == "ready"

    # Make sure the disk is ready before resizing
    wait_for_condition(15, 300, disk_poll_func)

    # resize disk
    retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"]
        + [
            "disk-resize",
            linode_id,
            disk_id,
            "--size",
            "50",
        ],
        retries=10,
        delay=15,
    )

    # Wait for the disk to be ready after resize
    wait_for_condition(15, 300, disk_poll_func)

    def disk_size_poll_func():
        size = exec_test_command(
            BASE_CMDS["linodes"]
            + [
                "disk-view",
                linode_id,
                disk_id,
                "--text",
                "--no-headers",
                "--format=size",
            ]
        )

        return size.strip() == "50"

    # Verify the resize actually took effect
    wait_for_condition(15, 300, disk_size_poll_func)

    # clone disk
    res = retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"]
        + [
            "disk-clone",
            linode_id,
            disk_id,
            "--text",
        ],
        retries=10,
        delay=15,
    )

    headers = ["id", "label", "status", "size", "filesystem", "disk_encryption"]

    assert_headers_in_lines(headers, res.splitlines())

    assert "Copy of" in res
    assert "50" in res

    label = get_random_text(5) + "disk"

    # create new disk
    res = retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"]
        + [
            "disk-create",
            linode_id,
            "--size",
            "15",
            "--label",
            label,
            "--text",
        ],
        retries=3,
        delay=10,
    )

    headers = ["id", "label", "status", "size", "filesystem", "disk_encryption"]

    assert_headers_in_lines(headers, res.splitlines())

    assert label in res
    assert "15" in res


def test_disk_reset_password(linode_instance_disk_tests):
    linode_id = linode_instance_disk_tests
    disk_id = get_disk_ids(linode_id)[0]

    retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"]
        + [
            "disk-reset-password",
            linode_id,
            disk_id,
            "--password",
            "ThIsIsRanDomPaSsWoRD",
            "--text",
        ],
        retries=3,
        delay=10,
    )


def test_disk_update(linode_instance_disk_tests):
    linode_id = linode_instance_disk_tests
    disk_id = get_disk_ids(linode_id)[0]

    update_label = get_random_text(5) + "newdisk"

    res = retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"]
        + [
            "disk-update",
            linode_id,
            disk_id,
            "--label",
            update_label,
            "--text",
        ],
        retries=3,
        delay=10,
    )

    headers = ["id", "label", "status", "size", "filesystem", "disk_encryption"]

    assert_headers_in_lines(headers, res.splitlines())
    assert update_label in res


def test_disks_list(linode_instance_disk_tests):
    linode_id = linode_instance_disk_tests

    res = retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"]
        + [
            "disks-list",
            linode_id,
            "--text",
        ]
    )

    headers = ["id", "label", "status", "size", "filesystem", "disk_encryption"]

    assert_headers_in_lines(headers, res.splitlines())
