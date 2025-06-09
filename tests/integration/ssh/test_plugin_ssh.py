import json
import subprocess
from sys import platform
from typing import Any, Dict, Optional

import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    COMMAND_JSON_OUTPUT,
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
    wait_for_condition,
)

TEST_REGION = get_random_region_with_caps(required_capabilities=["Linodes"])
TEST_IMAGE = "linode/ubuntu24.10"
TEST_TYPE = "g6-nanode-1"
TEST_ROOT_PASS = "r00tp@ss!long-long-and-longer"

BASE_CMD = ["linode-cli", "ssh"]


INSTANCE_WAIT_TIMEOUT_SECONDS = 120
SSH_WAIT_TIMEOUT_SECONDS = 80
POLL_INTERVAL = 5


@pytest.fixture
def target_instance(ssh_key_pair_generator, linode_cloud_firewall):
    instance_label = f"cli-test-{get_random_text(length=6)}"

    pubkey_file, privkey_file = ssh_key_pair_generator

    with open(pubkey_file, "r") as f:
        pubkey = f.read().rstrip()

    output = exec_test_command(
        BASE_CMDS["linodes"]
        + [
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
            "--firewall_id",
            linode_cloud_firewall,
        ]
        + COMMAND_JSON_OUTPUT
    )

    instance_json = json.loads(output)[0]

    yield instance_json

    delete_target_id(target="linodes", id=str(instance_json["id"]))


@pytest.mark.skipif(platform == "win32", reason="Test N/A on Windows")
def test_help():
    output = exec_test_command(BASE_CMDS["ssh"] + ["--help"])

    assert "[USERNAME@]LABEL" in output
    assert "uses the Linode's SLAAC address for SSH" in output


@pytest.mark.skipif(platform == "win32", reason="Test N/A on Windows")
def test_ssh_instance_provisioning(target_instance: Dict[str, Any]):
    output = exec_failing_test_command(
        BASE_CMDS["ssh"] + ["root@" + target_instance["label"]], expected_code=2
    )

    assert "is not running" in output


@pytest.mark.smoke
@pytest.mark.skipif(platform == "win32", reason="Test N/A on Windows")
def test_ssh_instance_ready(
    ssh_key_pair_generator, target_instance: Dict[str, Any]
):
    pubkey, privkey = ssh_key_pair_generator

    process: Optional[subprocess.CompletedProcess] = None
    instance_data = {}

    def instance_poll_func():
        nonlocal instance_data
        nonlocal process

        output = exec_test_command(
            BASE_CMDS["linodes"]
            + ["view", str(target_instance["id"])]
            + COMMAND_JSON_OUTPUT
        )
        instance_data = json.loads(output)[0]

        return instance_data["status"] == "running"

    def ssh_poll_func():
        exec_test_command(
            BASE_CMDS["ssh"]
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

    # Wait for the instance to be ready
    wait_for_condition(
        POLL_INTERVAL, INSTANCE_WAIT_TIMEOUT_SECONDS, instance_poll_func
    )

    assert instance_data["status"] == "running"

    # Wait for SSH to be available
    wait_for_condition(POLL_INTERVAL, SSH_WAIT_TIMEOUT_SECONDS, ssh_poll_func)
