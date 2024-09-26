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
    get_random_text,
)
from tests.integration.linodes.helpers_linodes import (
    DEFAULT_LINODE_TYPE,
    DEFAULT_RANDOM_PASS,
    DEFAULT_REGION,
    DEFAULT_TEST_IMAGE,
    create_linode_and_wait,
)

DOMAIN_BASE_CMD = ["linode-cli", "domains"]
LINODE_BASE_CMD = ["linode-cli", "linodes"]
NODEBALANCER_BASE_CMD = ["linode-cli", "nodebalancers"]


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

    firewall_id = exec_test_command(command).stdout.decode().rstrip()

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
    generate_test_file: Callable[[Optional[str], Optional[str]], Path]
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


# test helper specific to Domains test suite
@pytest.fixture
def master_domain():
    timestamp = str(time.time_ns())

    domain_id = (
        exec_test_command(
            DOMAIN_BASE_CMD
            + [
                "create",
                "--type",
                "master",
                "--domain",
                timestamp + "example.com",
                "--soa_email",
                "pthiel_test@linode.com",
                "--text",
                "--no-header",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield domain_id

    delete_target_id("domains", id=domain_id)


@pytest.fixture
def slave_domain():
    timestamp = str(time.time_ns())

    domain_id = (
        exec_test_command(
            DOMAIN_BASE_CMD
            + [
                "create",
                "--type",
                "slave",
                "--domain",
                timestamp + "-example.com",
                "--master_ips",
                "1.1.1.1",
                "--text",
                "--no-header",
                "--delimiter",
                ",",
                "--format=id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield domain_id

    delete_target_id("domains", domain_id)


# Test helpers specific to Linodes test suite
@pytest.fixture
def linode_with_label(linode_cloud_firewall):
    timestamp = str(time.time_ns())
    label = "cli" + timestamp
    result = (
        exec_test_command(
            LINODE_BASE_CMD
            + [
                "create",
                "--type",
                "g6-nanode-1",
                "--region",
                "us-ord",
                "--image",
                DEFAULT_TEST_IMAGE,
                "--label",
                label,
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--firewall_id",
                linode_cloud_firewall,
                "--text",
                "--delimiter",
                ",",
                "--no-headers",
                "--format",
                "label,region,type,image,id",
                "--no-defaults",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield result
    res_arr = result.split(",")
    linode_id = res_arr[4]
    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture
def linode_min_req(linode_cloud_firewall):
    result = (
        exec_test_command(
            LINODE_BASE_CMD
            + [
                "create",
                "--type",
                "g6-nanode-1",
                "--region",
                "us-ord",
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--firewall_id",
                linode_cloud_firewall,
                "--no-defaults",
                "--text",
                "--delimiter",
                ",",
                "--no-headers",
                "--format",
                "id,region,type",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield result

    res_arr = result.split(",")
    linode_id = res_arr[0]
    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture
def linode_wo_image(linode_cloud_firewall):
    label = "cli" + str(int(time.time()) + randint(10, 1000))
    linode_id = (
        exec_test_command(
            LINODE_BASE_CMD
            + [
                "create",
                "--no-defaults",
                "--label",
                label,
                "--type",
                DEFAULT_LINODE_TYPE,
                "--region",
                DEFAULT_REGION,
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--firewall_id",
                linode_cloud_firewall,
                "--format",
                "id",
                "--no-headers",
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture
def linode_backup_enabled(linode_cloud_firewall):
    # create linode with backups enabled
    linode_id = (
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "create",
                "--backups_enabled",
                "true",
                "--type",
                DEFAULT_LINODE_TYPE,
                "--region",
                DEFAULT_REGION,
                "--image",
                DEFAULT_TEST_IMAGE,
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--firewall_id",
                linode_cloud_firewall,
                "--text",
                "--no-headers",
                "--format=id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield linode_id

    delete_target_id("linodes", linode_id)


@pytest.fixture
def snapshot_of_linode():
    timestamp = str(time.time_ns())
    # get linode id after creation and wait for "running" status
    linode_id = create_linode_and_wait()
    new_snapshot_label = "test_snapshot" + timestamp

    result = exec_test_command(
        LINODE_BASE_CMD
        + [
            "snapshot",
            linode_id,
            "--label",
            new_snapshot_label,
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
        ]
    ).stdout.decode()

    yield linode_id, new_snapshot_label

    delete_target_id("linodes", linode_id)


# Test helpers specific to Nodebalancers test suite
@pytest.fixture
def nodebalancer_with_default_conf(linode_cloud_firewall):
    result = (
        exec_test_command(
            NODEBALANCER_BASE_CMD
            + [
                "create",
                "--region",
                "us-ord",
                "--firewall_id",
                linode_cloud_firewall,
                "--text",
                "--delimiter",
                ",",
                "--format",
                "id,label,region,hostname,client_conn_throttle",
                "--suppress-warnings",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield result

    res_arr = result.split(",")
    nodebalancer_id = res_arr[0]
    delete_target_id(target="nodebalancers", id=nodebalancer_id)


def get_regions_with_capabilities(capabilities):
    regions = (
        exec_test_command(
            [
                "linode-cli",
                "regions",
                "ls",
                "--text",
                "--no-headers",
                "--format=id,capabilities",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    regions = regions.split("\n")

    regions_with_all_caps = []

    for region in regions:
        region_name = region.split()[0]
        if all(capability in region for capability in capabilities):
            regions_with_all_caps.append(region_name)

    return regions_with_all_caps


def create_vpc_w_subnet():
    """
    Creates and returns a VPC and a corresponding subnet.

    This is not directly implemented as a fixture because the teardown
    order cannot be guaranteed, causing issues when attempting to
    assign Linodes to a VPC in a separate fixture.

    See: https://github.com/pytest-dev/pytest/issues/1216
    """

    region = get_regions_with_capabilities(["VPCs"])[0]
    vpc_label = str(time.time_ns()) + "label"
    subnet_label = str(time.time_ns()) + "label"

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
        .stdout.decode()
        .rstrip()
    )[0]

    return vpc_json


@pytest.mark.smoke
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "smoke: mark test as part of smoke test suite"
    )


@pytest.fixture
def support_test_linode_id(linode_cloud_firewall):
    timestamp = str(time.time_ns())
    label = "cli" + timestamp

    res = (
        exec_test_command(
            LINODE_BASE_CMD
            + [
                "create",
                "--type",
                "g6-nanode-1",
                "--region",
                "us-mia",
                "--image",
                DEFAULT_TEST_IMAGE,
                "--label",
                label,
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--firewall_id",
                linode_cloud_firewall,
                "--text",
                "--delimiter",
                ",",
                "--no-headers",
                "--format",
                "id",
                "--no-defaults",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    linode_id = res

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)
