import time

from tests.integration.helpers import exec_test_command

DEFAULT_RANDOM_PASS = (
    exec_test_command(["openssl", "rand", "-base64", "32"])
    .stdout.decode()
    .rstrip()
)
DEFAULT_REGION = "us-ord"

DEFAULT_TEST_IMAGE = (
    exec_test_command(
        [
            "linode-cli",
            "images",
            "list",
            "--text",
            "--format",
            "id",
            "--no-headers",
            "--is_public",
            "True",
        ]
    )
    .stdout.decode()
    .rstrip()
    .splitlines()[0]
)

DEFAULT_LINODE_TYPE = (
    exec_test_command(
        [
            "linode-cli",
            "linodes",
            "types",
            "--text",
            "--no-headers",
            "--format",
            "id",
        ]
    )
    .stdout.decode()
    .rstrip()
    .splitlines()[0]
)

DEFAULT_LABEL = "cli-default"

BASE_CMD = ["linode-cli", "linodes"]


def wait_until(linode_id: "str", timeout, status: "str", period=5):
    must_end = time.time() + timeout
    while time.time() < must_end:
        result = exec_test_command(
            [
                "linode-cli",
                "linodes",
                "view",
                linode_id,
                "--format",
                "status",
                "--text",
                "--no-headers",
            ]
        ).stdout.decode()
        if status in result:
            return True
        time.sleep(period)
    return False


def create_linode(
    firewall_id: str,
    test_region=DEFAULT_REGION,
    disk_encryption=False,
    interface_generation: str = None,
    interfaces: str = None,
):
    # Base command
    command = [
        "linode-cli",
        "linodes",
        "create",
        "--type",
        DEFAULT_LINODE_TYPE,
        "--region",
        test_region,
        "--image",
        DEFAULT_TEST_IMAGE,
        "--root_pass",
        DEFAULT_RANDOM_PASS,
        "--firewall_id",
        firewall_id,
        "--disk_encryption",
        "enabled" if disk_encryption else "disabled",
    ]

    if interface_generation:
        command.extend(["--interface_generation", interface_generation])

    if interfaces:
        command.extend(["--interfaces", interfaces])

    command.extend(["--format=id", "--text", "--no-headers"])

    linode_id = exec_test_command(command).stdout.decode().rstrip()

    return linode_id


def create_linode_backup_disabled(
    firewall_id: "str", test_region=DEFAULT_REGION
):
    result = set_backups_enabled_in_account_settings(toggle=False)

    # create linode
    linode_id = (
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "create",
                "--type",
                DEFAULT_LINODE_TYPE,
                "--region",
                test_region,
                "--image",
                DEFAULT_TEST_IMAGE,
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--firewall_id",
                firewall_id,
                "--format=id",
                "--text",
                "--no-headers",
                "--backups_enabled",
                "false",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    return linode_id


def shutdown_linodes():
    linode_ids = (
        exec_test_command(
            [
                BASE_CMD,
                "linodes",
                "list",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )

    for id in linode_ids:
        exec_test_command(["linode-cli", "linodes", "shutdown", id])


def remove_linodes():
    linode_ids = (
        exec_test_command(
            [
                BASE_CMD,
                "linodes",
                "list",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )

    for id in linode_ids:
        exec_test_command(["linode-cli", "linodes", "delete", id])


def create_linode_and_wait(
    firewall_id: "str",
    ssh_key="",
    test_plan=DEFAULT_LINODE_TYPE,
    test_image=DEFAULT_TEST_IMAGE,
    test_region=DEFAULT_REGION,
    disk_encryption=False,
):
    # Base command
    command = [
        "linode-cli",
        "linodes",
        "create",
        "--type",
        test_plan,
        "--region",
        test_region,
        "--image",
        test_image,
        "--root_pass",
        DEFAULT_RANDOM_PASS,
        "--firewall_id",
        firewall_id,
        "--format=id",
        "--backups_enabled",
        "true",
        "--disk_encryption",
        "enabled" if disk_encryption else "disabled",
        "--text",
        "--no-headers",
    ]

    # Add SSH key if provided
    if ssh_key:
        command.extend(["--authorized_keys", ssh_key])

    linode_id = exec_test_command(command).stdout.decode().strip()

    # wait until linode is running, wait_until returns True when it is in running state
    result = wait_until(linode_id=linode_id, timeout=240, status="running")

    assert result, "linode failed to change status to running"

    return linode_id


def set_backups_enabled_in_account_settings(toggle: bool):
    command = [
        "linode-cli",
        "account",
        "settings-update",
        "--format",
        "backups_enabled",
        "--text",
        "--no-headers",
    ]

    if toggle:
        command.extend(["--backups_enabled", "true"])
    else:
        command.extend(["--backups_enabled", "false"])

    result = exec_test_command(command).stdout.decode().rstrip()

    return result


def get_disk_ids(linode_id):
    disk_ids = (
        exec_test_command(
            BASE_CMD
            + [
                "disks-list",
                linode_id,
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )

    return disk_ids
