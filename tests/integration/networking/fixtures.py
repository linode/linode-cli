import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
)
from tests.integration.linodes.helpers import (
    DEFAULT_REGION,
    create_linode,
    create_linode_and_wait,
)


@pytest.fixture
def create_reserved_ip(request):
    tags = getattr(request, "param", None)
    command = BASE_CMDS["networking"] + [
        "reserved-ip-add",
        "--region",
        DEFAULT_REGION,
        "--text",
        "--delimiter",
        ","
    ]

    if tags:
        command += ["--tags", tags]

    headers, values = get_command_heads_and_vals(command)
    yield headers, values

    delete_target_id("networking", values[0], "reserved-ip-delete")


@pytest.fixture(scope="package")
def test_linode_id(linode_cloud_firewall):
    linode_id = create_linode_and_wait(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="package")
def test_linode_id_shared_ipv4(linode_cloud_firewall):
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


def get_command_heads_and_vals(command):
    result = exec_test_command(command).splitlines()
    headers = [item for item in result[0].split(",")]
    values = [item for item in result[1].split(",")]

    return headers, values