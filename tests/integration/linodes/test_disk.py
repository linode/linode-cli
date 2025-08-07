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


def test_disk_resize_clone_and_create(linode_instance_disk_tests):
    linode_id = linode_instance_disk_tests

    disk_id = get_disk_ids(linode_id=linode_id)[1]

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
        retries=3,
        delay=10,
    )

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

        return status == "ready"

    # Wait for the instance to be ready
    wait_for_condition(15, 150, disk_poll_func)

    # clone disk
    res = retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"]
        + [
            "disk-clone",
            linode_id,
            disk_id,
            "--text",
        ],
        retries=3,
        delay=10,
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
    disk_id = get_disk_ids(linode_id)[1]

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
    disk_id = get_disk_ids(linode_id)[1]

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
