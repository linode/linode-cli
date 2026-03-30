import json
import random
import re
import subprocess
import time
from string import ascii_lowercase
from typing import Callable, Container, Iterable, List, TypeVar

from linodecli.exit_codes import ExitCodes

BASE_URL = "https://api.linode.com/v4/"
INVALID_HOST = "https://wrongapi.linode.com"
SUCCESS_STATUS_CODE = 0
FAILED_STATUS_CODE = 256
COMMAND_JSON_OUTPUT = ["--suppress-warnings", "--no-defaults", "--json"]

# TypeVars for generic type hints below
T = TypeVar("T")

MODULES = [
    "account",
    "alerts",
    "domains",
    "linodes",
    "nodebalancers",
    "betas",
    "databases",
    "domains",
    "events",
    "image",
    "images",
    "image-sharegroups",
    "image-upload",
    "firewalls",
    "kernels",
    "linodes",
    "lke",
    "longview",
    "maintenance",
    "managed",
    "monitor",
    "networking",
    "obj",
    "object-storage",
    "placement",
    "profile",
    "regions",
    "ssh",
    "stackscripts",
    "tickets",
    "tags",
    "users",
    "vlans",
    "volumes",
    "vpcs",
]
BASE_CMDS = {module: ["linode-cli", module] for module in MODULES}


def get_random_text(length: int = 10):
    return "".join(random.choice(ascii_lowercase) for _ in range(length))


def wait_for_condition(interval: int, timeout: int, condition: Callable, *args):
    start_time = time.time()
    while True:
        result = condition(*args)

        if result:
            break

        if time.time() - start_time > timeout:
            raise TimeoutError("SSH timeout expired")

        # Evil
        time.sleep(interval)


def exec_test_command(args: List[str]):
    process = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {process.returncode}\n"
            f"Command: {' '.join(args)}\n"
            f"Stdout:\n{process.stdout}\n"
            f"Stderr:\n{process.stderr}"
        )
    return process.stdout.rstrip()


def exec_failing_test_command(
    args: List[str], expected_code: int = ExitCodes.REQUEST_FAILED
):
    process = subprocess.run(args, stderr=subprocess.PIPE, text=True)

    if process.returncode != expected_code:
        raise AssertionError(
            f"Expected exit code {expected_code}, got {process.returncode}\n"
            f"Command: {' '.join(args)}\n"
            f"Stdout:\n{process.stdout}\n"
            f"Stderr: {process.stderr}"
        )

    return process.stderr.rstrip()


# Delete/Remove helper functions (mainly used in clean-ups after tests)
def delete_target_id(
    target: str,
    id: str,
    delete_command: str = "delete",
    service_type: str = None,
    use_retry: bool = False,
    retries: int = 3,
    delay: int = 80,
):
    if service_type:
        command = ["linode-cli", target, delete_command, service_type, id]
    else:
        command = ["linode-cli", target, delete_command, id]

    if use_retry:
        last_exc = None
        for attempt in range(retries):
            try:
                subprocess.run(
                    command,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                return  # success
            except Exception as e:
                last_exc = e
                if attempt < retries - 1:
                    time.sleep(delay)
        # If all retries fail, raise
        raise RuntimeError(
            f"Error executing command '{' '.join(command)}' after {retries} retries: {last_exc}"
        )

    try:
        subprocess.run(
            command,
            check=True,  # Raises CalledProcessError on non-zero exit
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception as e:
        raise RuntimeError(
            f"Error executing command '{' '.join(command)}': {e}"
        )


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
        process = subprocess.run(args, stdout=subprocess.PIPE, text=True)

        # Check if the command succeeded
        if process.returncode == 0:
            return process.stdout.rstrip()
        else:
            print(
                f"Attempt {attempt + 1} failed, retrying in {delay} seconds..."
            )
            time.sleep(delay)

    assert process.returncode == 0, f"Command failed after {retries} retries"
    return process.stdout.rstrip()


def get_random_region_with_caps(
    required_capabilities: List[str],
    site_type: str = "core",
    valid_regions: List[str] = None,
):
    json_regions_data = exec_test_command(
        ["linode-cli", "regions", "ls", "--json"]
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

    # To filter out regions that cannot be used for the Linode resource
    if valid_regions:
        matching_region_ids = [reg for reg in matching_region_ids if reg in valid_regions]

    return random.choice(matching_region_ids) if matching_region_ids else None


def assert_help_actions_list(expected_actions, help_output):
    output_actions = re.findall(r"│\s(\S+(?:,\s)?\S+)\s*│", help_output)
    for expected_action in expected_actions:
        assert expected_action in output_actions


def view_command_attribute(
    command: str, action: str, item_id: str, attribute: str
) -> str:
    return exec_test_command(
        BASE_CMDS[command]
        + [
            action,
            item_id,
            "--text",
            "--no-header",
            "--format",
            attribute,
        ]
    )


def check_attribute_value(
    command: str, action: str, item_id: str, attribute: str, expected_val: str
) -> bool:
    result = view_command_attribute(command, action, item_id, attribute)
    return expected_val in result
