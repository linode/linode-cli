import json
import time

import pytest

from tests.integration.conftest import (
    create_vpc_w_subnet,
)
from tests.integration.helpers import delete_target_id, exec_test_command
from tests.integration.linodes.helpers_linodes import (
    BASE_CMD,
    DEFAULT_LABEL,
    DEFAULT_RANDOM_PASS,
    DEFAULT_TEST_IMAGE,
)

timestamp = str(time.time_ns())
linode_label = DEFAULT_LABEL + timestamp


@pytest.fixture
def linode_with_vpc_interface():
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


def test_with_vpc_interface(linode_with_vpc_interface):
    linode_json, vpc_json = linode_with_vpc_interface

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

    assert not public_interface["primary"]
    assert public_interface["purpose"] == "public"
