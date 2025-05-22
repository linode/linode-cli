import json
import time
from typing import Any, Dict

import pytest

from tests.integration.conftest import create_vpc_w_subnet
from tests.integration.helpers import delete_target_id, exec_test_command
from tests.integration.linodes.helpers_linodes import (
    BASE_CMD,
    DEFAULT_LABEL,
    DEFAULT_RANDOM_PASS,
    DEFAULT_TEST_IMAGE,
)

timestamp = str(time.time_ns())
linode_label = DEFAULT_LABEL + timestamp


@pytest.mark.skip("interface argument deprecated")
@pytest.fixture
def linode_with_vpc_interface(linode_cloud_firewall):
    vpc_json = create_vpc_w_subnet()

    vpc_region = vpc_json["region"]
    vpc_id = str(vpc_json["id"])
    subnet_id = str(vpc_json["subnets"][0]["id"])

    linode_json = json.loads(
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--type",
                "g6-nanode-1",
                "--region",
                vpc_region,
                "--image",
                DEFAULT_TEST_IMAGE,
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--firewall_id",
                linode_cloud_firewall,
                "--interfaces.purpose",
                "vpc",
                "--interfaces.primary",
                "true",
                "--interfaces.subnet_id",
                subnet_id,
                "--interfaces.ipv4.nat_1_1",
                "any",
                "--interfaces.ipv4.vpc",
                "10.0.0.5",
                "--interfaces.ip_ranges",
                json.dumps(["10.0.0.6/32"]),
                "--interfaces.purpose",
                "public",
                "--json",
                "--suppress-warnings",
            ]
        )
        .stdout.decode()
        .rstrip()
    )[0]

    yield linode_json, vpc_json

    delete_target_id(target="linodes", id=str(linode_json["id"]))
    delete_target_id(target="vpcs", id=vpc_id)


@pytest.fixture
def linode_with_vpc_interface_as_json(linode_cloud_firewall):
    vpc_json = create_vpc_w_subnet()

    vpc_region = vpc_json["region"]
    vpc_id = str(vpc_json["id"])
    subnet_id = int(vpc_json["subnets"][0]["id"])

    linode_json = json.loads(
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--type",
                "g6-nanode-1",
                "--region",
                vpc_region,
                "--image",
                DEFAULT_TEST_IMAGE,
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--firewall_id",
                linode_cloud_firewall,
                "--interfaces",
                json.dumps(
                    [
                        {
                            "purpose": "vpc",
                            "primary": True,
                            "subnet_id": subnet_id,
                            "ipv4": {"nat_1_1": "any", "vpc": "10.0.0.5"},
                            "ip_ranges": ["10.0.0.6/32"],
                        },
                        {"purpose": "public"},
                    ]
                ),
                "--json",
                "--suppress-warnings",
            ]
        )
        .stdout.decode()
        .rstrip()
    )[0]

    yield linode_json, vpc_json

    delete_target_id(target="linodes", id=str(linode_json["id"]))
    delete_target_id(target="vpcs", id=vpc_id)


def assert_interface_configuration(
    linode_json: Dict[str, Any], vpc_json: Dict[str, Any]
):
    config_json = json.loads(
        exec_test_command(
            BASE_CMD
            + [
                "configs-list",
                str(linode_json["id"]),
                "--json",
                "--suppress-warnings",
            ]
        )
        .stdout.decode()
        .rstrip()
    )[0]

    vpc_interface = config_json["interfaces"][0]
    public_interface = config_json["interfaces"][1]

    assert vpc_interface["primary"]
    assert vpc_interface["purpose"] == "vpc"
    assert vpc_interface["subnet_id"] == vpc_json["subnets"][0]["id"]
    assert vpc_interface["vpc_id"] == vpc_json["id"]
    assert vpc_interface["ipv4"]["vpc"] == "10.0.0.5"
    assert vpc_interface["ipv4"]["nat_1_1"] == linode_json["ipv4"][0]
    assert vpc_interface["ip_ranges"][0] == "10.0.0.6/32"

    assert not public_interface["primary"]
    assert public_interface["purpose"] == "public"


def test_with_vpc_interface(linode_with_vpc_interface):
    assert_interface_configuration(*linode_with_vpc_interface)


def test_with_vpc_interface_as_json(linode_with_vpc_interface_as_json):
    assert_interface_configuration(*linode_with_vpc_interface_as_json)
