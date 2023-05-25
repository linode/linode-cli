import os
import random
import subprocess
import time
from string import ascii_lowercase
from typing import Callable, List

BASE_URL = "https://api.linode.com/v4/"
INVALID_HOST = "https://wrongapi.linode.com"
SUCCESS_STATUS_CODE = 0
FAILED_STATUS_CODE = 256
INVALID_HOST = "https://wrongapi.linode.com"
SUCCESS_STATUS_CODE = 0

COMMAND_JSON_OUTPUT = ["--suppress-warnings", "--no-defaults", "--json"]


def get_random_text(length: int = 10):
    return "".join(random.choice(ascii_lowercase) for i in range(length))


def wait_for_condition(interval: int, timeout: int, condition: Callable):
    start_time = time.time()
    while True:
        if condition():
            break

        if time.time() - start_time > timeout:
            raise TimeoutError("SSH timeout expired")

        # Evil
        time.sleep(interval)


def exec_test_command(args: List[str]):
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
    )
    assert process.returncode == 0
    return process


def exec_failing_test_command(args: List[str], expected_code: int = 1):
    process = subprocess.run(
        args,
        stderr=subprocess.PIPE,
    )
    assert process.returncode == expected_code
    return process


# Delete/Remove helper functions (mainly used in clean-ups after test
def delete_all_domains():
    domain_ids = exec_test_command(
        [
            "linode-cli",
            "--text",
            "--no-headers",
            "domains",
            "list",
            "--format=id",
        ]
    ).stdout.decode()
    domain_id_arr = domain_ids.splitlines()

    for id in domain_id_arr:
        exec_test_command(["linode-cli", "domains", "delete", id])


def delete_tag(arg: str):
    result = exec_test_command(["linode-cli", "tags", "delete", arg])
    assert result.returncode == SUCCESS_STATUS_CODE


def delete_target_id(target: str, id: str):
    result = exec_test_command(["linode-cli", target, "delete", id])
    assert result.returncode == SUCCESS_STATUS_CODE


def remove_lke_clusters():
    cluster_ids = (
        os.popen(
            "linode-cli --text --no-headers lke clusters-list --format id | grep -v 'linuke-keep' | awk '{ print $1 }' |  xargs"
        )
        .read()
        .split()
    )
    for id in cluster_ids:
        exec_test_command(["linode-cli", "lke", "cluster-delete", id])


def delete_target_id(target: str, id: str):
    result = exec_test_command(["linode-cli", target, "delete", id])
    assert result.returncode == SUCCESS_STATUS_CODE


def remove_all(target: str):
    entity_ids = ""
    if target == "stackscripts":
        entity_ids = (
            os.popen(
                "linode-cli --is_public=false --text --no-headers "
                + target
                + " list --format='id,tags' | grep -v 'linuke-keep' | awk '{ print $1 }' | xargs"
            )
            .read()
            .split()
        )
    else:
        entity_ids = (
            os.popen(
                "linode-cli --text --no-headers "
                + target
                + " list --format='id,tags' | grep -v 'linuke-keep' | awk '{ print $1 }' | xargs"
            )
            .read()
            .split()
        )

    for id in entity_ids:
        exec_test_command(["linode-cli", target, "delete", id])


def exec_test_command(args: List[str]):
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
    )
    assert process.returncode == 0
    return process


def exec_failing_test_command(args: List[str]):
    process = subprocess.run(
        args,
        stderr=subprocess.PIPE,
    )
    assert process.returncode == 1
    return process
