import os
import re
import time
from sys import platform

import pytest

from tests.integration.helpers import delete_target_id, exec_test_command
from tests.integration.linodes.helpers_linodes import create_linode_and_wait

BASE_CMD = ["linode-cli", "ssh"]
NUM_OF_RETRIES = 10
SSH_SLEEP_PERIOD = 50


@pytest.mark.skipif(platform == "win32", reason="Test N/A on Windows")
@pytest.fixture(scope="package")
def linode_in_running_state(ssh_key_pair_generator, cloud_init_firewall):
    pubkey_file, privkey_file = ssh_key_pair_generator

    with open(pubkey_file, "r") as f:
        pubkey = f.read().rstrip()

    res = (
        exec_test_command(
            [
                "linode-cli",
                "images",
                "list",
                "--format",
                "id",
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    alpine_image = re.findall("linode/alpine[^\s]+", res)[0]

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
        .splitlines()[0]
    )

    linode_id = create_linode_and_wait(
        test_plan=plan,
        test_image=alpine_image,
        ssh_key=pubkey,
        firewall_id=cloud_init_firewall,
    )

    yield linode_id
    delete_target_id(target="linodes", id=linode_id)


@pytest.mark.skipif(platform == "win32", reason="Test N/A on Windows")
def test_display_ssh_plugin_usage_info():
    result = exec_test_command(BASE_CMD + ["-h"]).stdout.decode()
    assert "[USERNAME@]LABEL" in result
    assert "uses the Linode's SLAAC address for SSH" in result


@pytest.mark.skipif(platform == "win32", reason="Test N/A on Windows")
def test_fail_to_ssh_to_nonexistent_linode():
    os.system("linode-cli ssh root@aasdkjlf 2>&1 | tee /tmp/output_file.txt")

    result = os.popen("cat /tmp/output_file.txt").read().rstrip()

    assert "No Linode found for label aasdkjlf" in result


@pytest.mark.skipif(platform == "win32", reason="Test N/A on Windows")
def test_ssh_to_linode_and_get_kernel_version(
    linode_in_running_state, ssh_key_pair_generator
):
    linode_id = linode_in_running_state
    pubkey_file, privkey_file = ssh_key_pair_generator

    linode_label = (
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "list",
                "--id",
                linode_id,
                "--format",
                "label",
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    time.sleep(SSH_SLEEP_PERIOD)

    output = os.popen(
        "linode-cli ssh root@"
        + linode_label
        + " -i "
        + privkey_file
        + " -o StrictHostKeyChecking=no -o IdentitiesOnly=yes uname -r"
    ).read()

    assert re.search("[0-9]\.[0-9]*\.[0-9]*-.*-virt", output)


@pytest.mark.skipif(platform == "win32", reason="Test N/A on Windows")
def test_check_vm_for_ipv4_connectivity(
    linode_in_running_state, ssh_key_pair_generator
):
    pubkey_file, privkey_file = ssh_key_pair_generator
    linode_id = linode_in_running_state
    linode_label = (
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "list",
                "--id",
                linode_id,
                "--format",
                "label",
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    time.sleep(SSH_SLEEP_PERIOD)

    output = os.popen(
        "linode-cli ssh root@"
        + linode_label
        + " -i "
        + privkey_file
        + ' -o StrictHostKeyChecking=no -o IdentitiesOnly=yes "ping -4 -W60 -c3 google.com"'
    ).read()

    assert "0% packet loss" in output
