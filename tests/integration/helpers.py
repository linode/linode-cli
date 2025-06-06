import json
import random
import subprocess
import time
from string import ascii_lowercase
from typing import Callable, Container, Iterable, List, TypeVar

from linodecli import ExitCodes
from linodecli.exit_codes import ExitCodes

BASE_URL = "https://api.linode.com/v4/"
INVALID_HOST = "https://wrongapi.linode.com"
SUCCESS_STATUS_CODE = 0
FAILED_STATUS_CODE = 256
COMMAND_JSON_OUTPUT = ["--suppress-warnings", "--no-defaults", "--json"]

# TypeVars for generic type hints below
T = TypeVar("T")


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
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {process.returncode}\n"
            f"Command: {' '.join(args)}\n"
            f"Stdout:\n{process.stdout.decode()}\n"
            f"Stderr:\n{process.stderr.decode()}"
        )
    return process


def exec_failing_test_command(
    args: List[str], expected_code: int = ExitCodes.REQUEST_FAILED
):
    process = subprocess.run(args, stderr=subprocess.PIPE)
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


def delete_target_id(target: str, id: str, delete_command: str = "delete"):
    command = ["linode-cli", target, delete_command, id]
    result = exec_test_command(command)
    assert result.returncode == SUCCESS_STATUS_CODE


def remove_lke_clusters():
    cluster_ids = (
        exec_test_command(
            [
                "linode-cli",
                "--text",
                "--no-headers",
                "lke",
                "clusters-list",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )
    for id in cluster_ids:
        exec_test_command(["linode-cli", "lke", "cluster-delete", id])


def remove_all(target: str):
    entity_ids = ""
    if target == "stackscripts":
        entity_ids = (
            exec_test_command(
                [
                    "linode-cli",
                    "--is_public=false",
                    "--text",
                    "--no-headers",
                    target,
                    "list",
                    "--format",
                    "id",
                ]
            )
            .stdout.decode()
            .splitlines()
        )
    else:
        entity_ids = (
            exec_test_command(
                [
                    "linode-cli",
                    "--text",
                    "--no-headers",
                    target,
                    "list",
                    "--format",
                    "id",
                ]
            )
            .stdout.decode()
            .splitlines()
        )

    for id in entity_ids:
        exec_test_command(["linode-cli", target, "delete", id])


def count_lines(text: str):
    return len(list(filter(len, text.split("\n"))))


def assert_headers_in_lines(headers, lines):
    for header in headers:
        assert header in lines[0]


def contains_at_least_one_of(target: Container[T], search_for: Iterable[T]):
    return any(v in target for v in search_for)


def retry_exec_test_command_with_delay(
    args: List[str], retries: int = 3, delay: int = 2
):
    for attempt in range(retries):
        process = subprocess.run(args, stdout=subprocess.PIPE)

        # Check if the command succeeded
        if process.returncode == 0:
            return process
        else:
            print(
                f"Attempt {attempt + 1} failed, retrying in {delay} seconds..."
            )
            time.sleep(delay)

    assert process.returncode == 0, f"Command failed after {retries} retries"
    return process


def get_random_region_with_caps(
    required_capabilities: List[str], site_type="core"
):
    json_regions_data = (
        exec_test_command(["linode-cli", "regions", "ls", "--json"])
        .stdout.decode()
        .strip()
    )

    # Parse regions JSON data
    regions = json.loads(json_regions_data)

    matching_regions = [
        region
        for region in regions
        if all(cap in region["capabilities"] for cap in required_capabilities)
        and region["site_type"] == site_type
    ]

    # Extract the region ids
    matching_region_ids = [region["id"] for region in matching_regions]

    return random.choice(matching_region_ids) if matching_region_ids else None


def get_cluster_id(label: str):
    cluster_id = (
        exec_test_command(
            [
                "linode-cli",
                "lke",
                "clusters-list",
                "--text",
                "--format=id",
                "--no-headers",
                "--label",
                label,
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    return cluster_id
