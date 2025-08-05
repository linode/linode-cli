import json
from typing import Any, Dict

from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
)
from tests.integration.linodes.fixtures import (  # noqa: F401
    linode_with_vpc_interface_as_json,
)


def assert_interface_configuration(
    linode_json: Dict[str, Any], vpc_json: Dict[str, Any]
):
    config_json = json.loads(
        exec_test_command(
            BASE_CMDS["linodes"]
            + [
                "configs-list",
                str(linode_json["id"]),
                "--json",
                "--suppress-warnings",
            ]
        )
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


def test_with_vpc_interface_as_json(linode_with_vpc_interface_as_json):
    assert_interface_configuration(*linode_with_vpc_interface_as_json)
