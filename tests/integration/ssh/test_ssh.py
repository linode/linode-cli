import os
import re
import time

import pytest

from tests.integration.helpers import exec_test_command
from tests.integration.linodes.helpers_linodes import (
    create_linode_and_wait,
    remove_linodes,
)

BASE_CMD = ["linode-cli", "ssh"]
NUM_OF_RETRIES = 10
SSH_SLEEP_PERIOD = 50


@pytest.fixture(scope="session", autouse=True)
def test_create_a_linode_in_running_state(ssh_key_pair_generator):
    pubkey_file, privkey_file = ssh_key_pair_generator

    with open(pubkey_file, "r") as f:
        pubkey = f.read().rstrip()

    alpine_image = (
        os.popen(
            "linode-cli images list --format id --text --no-headers | grep 'alpine' | xargs | awk '{ print $1 }'"
        )
        .read()
        .rstrip()
    )
    plan = (
        os.popen(
            "linode-cli linodes types --text --no-headers --format=id | xargs | awk '{ print $1 }'"
        )
        .read()
        .rstrip()
    )

    linode_id = create_linode_and_wait(
        test_plan=plan, test_image=alpine_image, ssh_key=pubkey
    )

    yield linode_id
    remove_linodes()


def test_display_ssh_plugin_usage_info():
    result = exec_test_command(BASE_CMD + ["-h"]).stdout.decode()
    assert "usage: linode-cli ssh [-h] [-6] [[USERNAME@]LABEL]" in result
    assert "positional arguments:" in result
    assert (
        "[USERNAME@]LABEL  The label of the Linode to SSH into, optionally with a"
        in result
    )
    assert "username before it in USERNAME@LABEL format. If no" in result
    assert "username is given, defaults to the current user." in result
    assert "option" in result
    assert "-h, --help        show this help message and exit" in result
    assert (
        "-6                If given, uses the Linode's SLAAC address for SSH."
        in result
    )


def test_fail_to_ssh_to_nonexistent_linode():
    os.system("linode-cli ssh root@aasdkjlf 2>&1 | tee /tmp/output_file.txt")

    result = os.popen("cat /tmp/output_file.txt").read().rstrip()

    assert "No Linode found for label aasdkjlf" in result


def test_ssh_to_linode_and_get_kernel_version(
    test_create_a_linode_in_running_state, ssh_key_pair_generator
):
    linode_id = test_create_a_linode_in_running_state
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


def test_check_vm_for_ipv4_connectivity(
    test_create_a_linode_in_running_state, ssh_key_pair_generator
):
    pubkey_file, privkey_file = ssh_key_pair_generator
    linode_id = test_create_a_linode_in_running_state
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
