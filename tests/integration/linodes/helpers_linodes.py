import os
import time

from tests.integration.helpers import exec_test_command

DEFAULT_RANDOM_PASS = (
    exec_test_command(["openssl", "rand", "-base64", "32"])
    .stdout.decode()
    .rstrip()
)
DEFAULT_REGION = "us-east"
DEFAULT_TEST_IMAGE = (
    os.popen(
        'linode-cli images list --format id --text --no-header | egrep "linode\/.*" | head -n 1'
    )
    .read()
    .rstrip()
)
DEFAULT_LINODE_TYPE = (
    os.popen(
        "linode-cli linodes types --text --no-headers --format='id' | xargs | awk '{ print $1 }'"
    )
    .read()
    .rstrip()
)
DEFAULT_LABEL = "cli-default"
BASE_CMD = ["linode-cli", "linodes"]


def generate_random_ssh_key():
    key_path = "/tmp/cli-e2e-key"
    os.popen("ssh-keygen -q -t rsa -N " " -f " + key_path)
    time.sleep(1)
    private_ssh_key = (
        exec_test_command(["cat", key_path]).stdout.decode().rstrip()
    )
    public_ssh_key = (
        exec_test_command(["cat", key_path + ".pub"]).stdout.decode().rstrip()
    )

    private_keypath = key_path
    public_keypath = key_path + ".pub"
    return private_ssh_key, public_ssh_key, private_keypath, public_keypath


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
    linode_type = (
        os.popen(
            "linode-cli linodes types --text --no-headers --format='id' | xargs | awk '{ print $1 }'"
        )
        .read()
        .rstrip()
    )
    test_image = (
        os.popen(
            'linode-cli images list --format id --text --no-header | egrep "linode\/.*" | head -n 1'
        )
        .read()
        .rstrip()
    )

    # create linode
    linode_id = (
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "create",
                "--type",
                linode_type,
                "--region",
                region,
                "--image",
                test_image,
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
        os.popen(
            'linode-cli --text --no-headers linodes list --format "id" | grep -v "linuke-keep" | awk "{ print $1 }" | xargs'
        )
        .read()
        .split()
    )
    for id in linode_ids:
        exec_test_command(["linode-cli", "linodes", "shutdown", id])


def remove_linodes():
    linode_ids = (
        os.popen(
            'linode-cli --text --no-headers linodes list --format "id" | grep -v "linuke-keep" | awk "{ print $1 }" | xargs'
        )
        .read()
        .split()
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
