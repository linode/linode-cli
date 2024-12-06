import pytest

from tests.integration.helpers import (
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
    retry_exec_test_command_with_delay,
    wait_for_condition,
)
from tests.integration.linodes.helpers_linodes import (
    BASE_CMD,
    create_linode_and_wait,
    get_disk_ids,
    wait_until,
)

TEST_REGION = get_random_region_with_caps(required_capabilities=["Linodes"])


@pytest.fixture(scope="session", autouse=True)
def linode_instance_disk_tests(linode_cloud_firewall):
    linode_id = create_linode_and_wait(
        firewall_id=linode_cloud_firewall,
        disk_encryption=False,
        test_region=TEST_REGION,
        test_plan="g6-standard-4",
    )

    retry_exec_test_command_with_delay(BASE_CMD + ["shutdown", linode_id])

    wait_until(linode_id=linode_id, timeout=240, status="offline")

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


def test_disk_resize_clone_and_create(linode_instance_disk_tests):
    linode_id = linode_instance_disk_tests

    disk_id = get_disk_ids(linode_id=linode_id)[1]

    # resize disk
    retry_exec_test_command_with_delay(
        BASE_CMD
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
        status = (
            exec_test_command(
                BASE_CMD
                + [
                    "disk-view",
                    linode_id,
                    disk_id,
                    "--text",
                    "--no-headers",
                    "--format=status",
                ]
            )
            .stdout.decode()
            .rstrip()
        )

        return status == "ready"

    # Wait for the instance to be ready
    wait_for_condition(15, 150, disk_poll_func)

    # clone disk
    res = (
        retry_exec_test_command_with_delay(
            BASE_CMD
            + [
                "disk-clone",
                linode_id,
                disk_id,
                "--text",
            ],
            retries=3,
            delay=10,
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "status", "size", "filesystem", "disk_encryption"]

    assert_headers_in_lines(headers, res.splitlines())

    assert "Copy of" in res
    assert "50" in res

    label = get_random_text(5) + "disk"

    # create new disk
    res = (
        retry_exec_test_command_with_delay(
            BASE_CMD
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
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "status", "size", "filesystem", "disk_encryption"]

    assert_headers_in_lines(headers, res.splitlines())

    assert label in res
    assert "15" in res
    # assert "disabled" in res


def test_disk_reset_password(linode_instance_disk_tests):
    linode_id = linode_instance_disk_tests
    disk_id = get_disk_ids(linode_id)[1]

    res = retry_exec_test_command_with_delay(
        BASE_CMD
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

    assert res.returncode == 0


def test_disk_update(linode_instance_disk_tests):
    linode_id = linode_instance_disk_tests
    disk_id = get_disk_ids(linode_id)[1]

    update_label = get_random_text(5) + "newdisk"

    res = (
        (
            retry_exec_test_command_with_delay(
                BASE_CMD
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
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "status", "size", "filesystem", "disk_encryption"]

    assert_headers_in_lines(headers, res.splitlines())
    assert update_label in res


def test_disks_list(linode_instance_disk_tests):
    linode_id = linode_instance_disk_tests

    res = (
        (
            retry_exec_test_command_with_delay(
                BASE_CMD
                + [
                    "disks-list",
                    linode_id,
                    "--text",
                ]
            )
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "status", "size", "filesystem", "disk_encryption"]

    assert_headers_in_lines(headers, res.splitlines())
