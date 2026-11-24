import json

import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    COMMAND_JSON_OUTPUT,
    delete_target_id,
    exec_test_command,
)
from tests.integration.linodes.helpers import (
    create_linode,
    create_linode_and_wait,
)
from tests.integration.linodes.fixtures import TEST_REGION  # noqa: F401


@pytest.fixture
def create_nat_gateway(request, name_generator):
    autoscaling = getattr(request, "param", True)
    label = name_generator("nat-gateway")
    result = json.loads(
        exec_test_command(
            BASE_CMDS["natgateways"]
            + [
                "natgateways-add",
                "--label",
                label,
                "--region",
                TEST_REGION,
                "--default_ports_per_interface",
                "4096",
                "--use_autoscaling",
                str(autoscaling),
            ]
            + COMMAND_JSON_OUTPUT
        )
    )[0]

    yield result, label

    delete_target_id("natgateways", str(result["id"]), "natgateways-delete")


@pytest.fixture
def create_nat_reserved_ip(request):
    command = [
        "linode-cli",
        "networking",
        "reserved-ip-add",
        "--region",
        TEST_REGION,
        "--json",
    ]
    result = json.loads(exec_test_command(command))[0]

    yield result

    delete_target_id("networking", result["address"], "reserved-ip-delete")


@pytest.fixture(scope="package")
def get_linode_id(linode_cloud_firewall):
    linode_id = create_linode_and_wait(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="package")
def get_linode_ids_shared_ipv4(linode_cloud_firewall):
    target_region = "us-mia"

    linode_ids = (
        create_linode(
            test_region=target_region, firewall_id=linode_cloud_firewall
        ),
        create_linode(
            test_region=target_region, firewall_id=linode_cloud_firewall
        ),
    )

    yield linode_ids

    for id_num in linode_ids:
        delete_target_id(target="linodes", id=id_num)
