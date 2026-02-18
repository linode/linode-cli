import json
from typing import Any, Dict

from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
    wait_for_condition,
)
from tests.integration.linodes.fixtures import (  # noqa: F401
    linode_with_vpc_interface_as_args,
    linode_with_vpc_interface_as_json,
)


def assert_interface_configuration(
    linode_json: Dict[str, Any], vpc_json: Dict[str, Any]
):
    linode_id = str(linode_json["id"])
    configs = []

    def fetch_configs():
        nonlocal configs
        configs = json.loads(
            exec_test_command(
                BASE_CMDS["linodes"]
                + [
                    "configs-list",
                    linode_id,
                    "--json",
                    "--suppress-warnings",
                ]
            )
        )
        return len(configs) > 0

    wait_for_condition(5, 180, fetch_configs)

    assert configs, f"No configs found for Linode {linode_id}"
    config_json = configs[0]

    interfaces = config_json["interfaces"]

    vpc_interface = next((i for i in interfaces if i["purpose"] == "vpc"), None)
    public_interface = next(
        (i for i in interfaces if i["purpose"] == "public"), None
    )

    assert (
        vpc_interface
    ), "Expected interface with purpose 'vpc' in configuration"
    assert (
        public_interface
    ), "Expected interface with purpose 'public' in configuration"
    assert vpc_interface["primary"]
    assert vpc_interface["purpose"] == "vpc"
    assert vpc_interface["subnet_id"] == vpc_json["subnets"][0]["id"]
    assert vpc_interface["vpc_id"] == vpc_json["id"]
    assert vpc_interface["ipv4"]["vpc"] == "10.0.0.5"
    assert vpc_interface["ipv4"]["nat_1_1"] == linode_json["ipv4"][0]
    assert vpc_interface["ip_ranges"][0] == "10.0.0.6/32"

    assert not public_interface["primary"]


def test_with_vpc_interface_as_args(linode_with_vpc_interface_as_args):
    assert_interface_configuration(*linode_with_vpc_interface_as_args)


def test_with_vpc_interface_as_json(linode_with_vpc_interface_as_json):
    assert_interface_configuration(*linode_with_vpc_interface_as_json)
