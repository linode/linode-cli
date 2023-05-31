import json
import subprocess
from typing import Any, Dict, List, Optional

import pytest

from tests.integration.helpers import (
    COMMAND_JSON_OUTPUT,
    get_random_text,
    wait_for_condition,
)

TEST_REGION = "us-southeast"
TEST_IMAGE = "linode/alpine3.16"
TEST_TYPE = "g6-nanode-1"
TEST_ROOT_PASS = "r00tp@ss!long-long-and-longer"

BASE_CMD = ["linode-cli", "ssh"]


INSTANCE_WAIT_TIMEOUT_SECONDS = 120
SSH_WAIT_TIMEOUT_SECONDS = 80
POLL_INTERVAL = 5


@pytest.fixture
def target_instance(ssh_key_pair_generator, platform_os_type):
    if platform_os_type == "Windows":
        pytest.skip("This pluggin is not supported on Windows")
    instance_label = f"cli-test-{get_random_text(length=6)}"

    pubkey_file, privkey_file = ssh_key_pair_generator

    with open(pubkey_file, "r") as f:
        pubkey = f.read().rstrip()

    process = exec_test_command(
        [
            "linode-cli",
            "linodes",
            "create",
            "--image",
            TEST_IMAGE,
            "--region",
            TEST_REGION,
            "--type",
            TEST_TYPE,
            "--label",
            instance_label,
            "--root_pass",
            TEST_ROOT_PASS,
            "--authorized_keys",
            pubkey,
        ]
        + COMMAND_JSON_OUTPUT
    )
    assert process.returncode == 0
    instance_json = json.loads(process.stdout.decode())[0]

    yield instance_json

    process = exec_test_command(
        ["linode-cli", "linodes", "rm", str(instance_json["id"])]
    )
    assert process.returncode == 0


def exec_test_command(args: List[str], timeout=None):
    process = subprocess.run(args, stdout=subprocess.PIPE, timeout=timeout)
    return process


def test_help():
    process = exec_test_command(BASE_CMD + ["--help"])
    output = process.stdout.decode()

    assert process.returncode == 0
    assert "[USERNAME@]LABEL" in output
    assert "uses the Linode's SLAAC address for SSH" in output


def test_ssh_instance_provisioning(target_instance: Dict[str, Any]):
    process = exec_test_command(BASE_CMD + ["root@" + target_instance["label"]])
    assert process.returncode == 2
    output = process.stdout.decode()

    assert "is not running" in output


def test_ssh_instance_ready(
    ssh_key_pair_generator, target_instance: Dict[str, Any]
):
    pubkey, privkey = ssh_key_pair_generator

    process: Optional[subprocess.CompletedProcess] = None
    instance_data = {}

    def instance_poll_func():
        nonlocal instance_data
        nonlocal process

        process = exec_test_command(
            ["linode-cli", "linodes", "view", str(target_instance["id"])]
            + COMMAND_JSON_OUTPUT
        )
        assert process.returncode == 0
        instance_data = json.loads(process.stdout.decode())[0]

        return instance_data["status"] == "running"

    def ssh_poll_func():
        nonlocal process
        process = exec_test_command(
            BASE_CMD
            + [
                "root@" + instance_data["label"],
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "IdentitiesOnly=yes",
                "-i",
                privkey,
                "echo 'hello world!'",
            ]
        )
        return process.returncode == 0

    # Wait for the instance to be ready
    wait_for_condition(
        POLL_INTERVAL, INSTANCE_WAIT_TIMEOUT_SECONDS, instance_poll_func
    )

    assert process.returncode == 0
    assert instance_data["status"] == "running"

    # Wait for SSH to be available
    wait_for_condition(POLL_INTERVAL, SSH_WAIT_TIMEOUT_SECONDS, ssh_poll_func)

    assert process.returncode == 0

    # Did we get a response from the instance?
    assert "hello world!" in process.stdout.decode()
