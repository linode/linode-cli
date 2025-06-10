# Use random integer as the start point here to avoid
# id conflicts when multiple testings are running.
import ipaddress
import json
import logging
import os
import subprocess
import tempfile
import time
from collections import defaultdict
from itertools import count
from pathlib import Path
from random import randint
from typing import Callable, Optional

import pytest
import requests

from linodecli import ENV_TOKEN_NAME
from tests.integration.helpers import (
    delete_target_id,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
)


@pytest.fixture(autouse=True, scope="session")
def linode_cloud_firewall():
    def is_valid_ipv4(address):
        try:
            ipaddress.IPv4Address(address)
            return True
        except ipaddress.AddressValueError:
            return False

    def is_valid_ipv6(address):
        try:
            ipaddress.IPv6Address(address)
            return True
        except ipaddress.AddressValueError:
            return False

    def get_public_ip(ip_version="ipv4"):
        url = (
            f"https://api64.ipify.org?format=json"
            if ip_version == "ipv6"
            else f"https://api.ipify.org?format=json"
        )
        response = requests.get(url)
        return str(response.json()["ip"])

    def create_inbound_rule(ipv4_address, ipv6_address):
        rule = [
            {
                "protocol": "TCP",
                "ports": "22",
                "addresses": {},
                "action": "ACCEPT",
            }
        ]
        if is_valid_ipv4(ipv4_address):
            rule[0]["addresses"]["ipv4"] = [f"{ipv4_address}/32"]

        if is_valid_ipv6(ipv6_address):
            rule[0]["addresses"]["ipv6"] = [f"{ipv6_address}/128"]

        return json.dumps(rule, indent=4)

    # Fetch the public IP addresses
    ipv4_address = get_public_ip("ipv4")
    ipv6_address = get_public_ip("ipv6")

    inbound_rule = create_inbound_rule(ipv4_address, ipv6_address)

    label = "cloud_firewall_" + str(int(time.time()))

    # Base command list
    command = [
        "linode-cli",
        "firewalls",
        "create",
        "--label",
        label,
        "--rules.outbound_policy",
        "ACCEPT",
        "--rules.inbound_policy",
        "DROP",
        "--text",
        "--no-headers",
        "--format",
        "id",
    ]

    if is_valid_ipv4(ipv4_address) or is_valid_ipv6(ipv6_address):
        command.extend(["--rules.inbound", inbound_rule])

    firewall_id = exec_test_command(command)

    yield firewall_id

    delete_target_id(target="firewalls", id=firewall_id)


@pytest.fixture(scope="session")
def _id_generators():
    return defaultdict(lambda: count(randint(0, 1000000)))


@pytest.fixture(scope="session")
def name_generator(_id_generators: dict):
    generator = lambda prefix: f"{prefix}-{next(_id_generators[prefix])}"
    return generator


@pytest.fixture(scope="session")
def ssh_key_pair_generator():
    key_dir = tempfile.TemporaryDirectory()

    # Generate the key pair
    process = subprocess.run(
        [
            "ssh-keygen",
            "-f",
            f"{key_dir.name}/key",
            "-b",
            "4096",
            "-q",
            "-t",
            "rsa",
            "-N",
            "",
        ],
        stdout=subprocess.PIPE,
    )
    assert process.returncode == 0

    yield f"{key_dir.name}/key.pub", f"{key_dir.name}/key"

    key_dir.cleanup()


@pytest.fixture(scope="session")
def token():
    token = os.getenv(ENV_TOKEN_NAME)
    if not token:
        logging.error(
            f"Token is required in the environment as {ENV_TOKEN_NAME}"
        )
    return token


@pytest.fixture
def generate_test_file(name_generator: Callable[[str], str]):
    test_files_dir = tempfile.TemporaryDirectory()

    def _generate_test_file(
        content: Optional[str] = None,
        filename: Optional[str] = None,
        size: Optional[int] = 100,
    ):
        if content is None:
            content = f"{get_random_text(size)}"
        if filename is None:
            filename = f"{name_generator('test-file')}.txt"
        file_path = Path(test_files_dir.name) / filename
        file_path = file_path.resolve()
        with open(file_path, "w") as f:
            f.write(content)
        return file_path

    yield _generate_test_file
    test_files_dir.cleanup()


@pytest.fixture
def generate_test_files(
    generate_test_file: Callable[[Optional[str], Optional[str]], Path],
):
    """
    Return a function that can generate files with random text.
    """

    def _generate_test_files(
        num: Optional[int] = 1, content: Optional[str] = None
    ):
        file_paths = [generate_test_file(content=content) for _ in range(num)]
        return file_paths

    return _generate_test_files


def create_vpc_w_subnet():
    """
    Creates and returns a VPC and a corresponding subnet.

    This is not directly implemented as a fixture because the teardown
    order cannot be guaranteed, causing issues when attempting to
    assign Linodes to a VPC in a separate fixture.

    See: https://github.com/pytest-dev/pytest/issues/1216
    """

    region = get_random_region_with_caps(required_capabilities=["VPCs"])
    vpc_label = get_random_text(5) + "label"
    subnet_label = get_random_text(5) + "label"

    vpc_json = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "vpcs",
                "create",
                "--label",
                vpc_label,
                "--region",
                region,
                "--subnets.ipv4",
                "10.0.0.0/24",
                "--subnets.label",
                subnet_label,
                "--json",
                "--suppress-warnings",
            ]
        )
    )[0]

    return vpc_json


@pytest.mark.smoke
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "smoke: mark test as part of smoke test suite"
    )
