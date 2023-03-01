import json
import subprocess
import time
from typing import Any, Dict, List

import pytest
from helpers import COMMAND_JSON_OUTPUT, get_random_text

TEST_REGION = "us-southeast"
TEST_IMAGE = "linode/alpine3.16"
TEST_TYPE = "g6-nanode-1"
TEST_ROOT_PASS = "r00tp@ss!"

BASE_CMD = ["linode-cli", "ssh"]


@pytest.fixture
def target_instance():
    instance_label = f"cli-test-{get_random_text(length=6)}"
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
    assert "positional arguments" in output
    assert "optional arguments" in output


def test_ssh_instance_provisioning(target_instance: Dict[str, Any]):
    process = exec_test_command(BASE_CMD + ["root@" + target_instance["label"]])
    assert process.returncode == 2
    output = process.stdout.decode()

    assert "is not running" in output


def test_ssh_instance_ready(target_instance: Dict[str, Any]):
    instance_data = target_instance

    # Wait for the instance to be running
    continue_polling = True
    while continue_polling:
        process = exec_test_command(
            ["linode-cli", "linodes", "view", str(target_instance["id"])]
            + COMMAND_JSON_OUTPUT
        )
        assert process.returncode == 0
        instance_data = json.loads(process.stdout.decode())[0]

        continue_polling = instance_data["status"] != "running"

        # Evil
        time.sleep(5)

    assert instance_data["status"] == "running"

    p = subprocess.Popen(BASE_CMD + ["root@" + instance_data["label"]])

    # Also evil; just checking that the process is
    # continually reading stdin (assumed SSH)
    time.sleep(3)

    # Is the process still alive?
    assert p.poll() is None
    p.terminate()
