import time

from tests.integration.helpers import exec_test_command

DEFAULT_RANDOM_PASS = (
    exec_test_command(["openssl", "rand", "-base64", "32"])
    .stdout.decode()
    .rstrip()
)
DEFAULT_REGION = "us-east"

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


def create_linode():
    region = "us-east"

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
                region,
                "--image",
                DEFAULT_TEST_IMAGE,
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--format=id",
                "--text",
                "--no-headers",
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
    test_plan=DEFAULT_LINODE_TYPE, test_image=DEFAULT_TEST_IMAGE, ssh_key=""
):
    linode_type = test_plan

    # key_pair = generate_random_ssh_key()

    output = ""
    # if ssh key is successfully generated
    if ssh_key:
        output = (
            exec_test_command(
                [
                    "linode-cli",
                    "linodes",
                    "create",
                    "--type",
                    linode_type,
                    "--region",
                    "us-east",
                    "--image",
                    test_image,
                    "--root_pass",
                    DEFAULT_RANDOM_PASS,
                    "--authorized_keys",
                    ssh_key,
                    "--format=id",
                    "--backups_enabled",
                    "true",
                    "--text",
                    "--no-headers",
                ]
            )
            .stdout.decode()
            .rstrip()
        )
    else:
        output = (
            exec_test_command(
                [
                    "linode-cli",
                    "linodes",
                    "create",
                    "--type",
                    linode_type,
                    "--region",
                    "us-east",
                    "--image",
                    test_image,
                    "--root_pass",
                    DEFAULT_RANDOM_PASS,
                    "--format=id",
                    "--backups_enabled",
                    "true",
                    "--text",
                    "--no-headers",
                ]
            )
            .stdout.decode()
            .rstrip()
        )
    linode_id = output

    # wait until linode is running
    assert (
        wait_until(linode_id=linode_id, timeout=240, status="running"),
        "linode failed to change status to running",
    )

    return linode_id
