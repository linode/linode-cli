import pytest

from tests.integration.conftest import create_vpc_w_subnet
from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
)


@pytest.fixture
def test_vpc_w_subnet():
    vpc_json = create_vpc_w_subnet()
    vpc_id = str(vpc_json["id"])

    yield vpc_id

    delete_target_id(target="vpcs", id=vpc_id)


@pytest.fixture
def test_vpc_wo_subnet():
    region = get_random_region_with_caps(required_capabilities=["VPCs"])

    label = get_random_text(5) + "-label"

    vpc_id = exec_test_command(
        BASE_CMDS["vpcs"]
        + [
            "create",
            "--label",
            label,
            "--region",
            region,
            "--no-headers",
            "--text",
            "--format=id",
        ]
    )

    yield vpc_id

    delete_target_id(target="vpcs", id=vpc_id)


@pytest.fixture
def test_subnet(test_vpc_wo_subnet):
    vpc_id = test_vpc_wo_subnet
    subnet_label = get_random_text(5) + "-label"
    res = exec_test_command(
        BASE_CMDS["vpcs"]
        + [
            "subnet-create",
            "--label",
            subnet_label,
            "--ipv4",
            "10.0.0.0/24",
            vpc_id,
            "--text",
            "--no-headers",
            "--delimiter=,",
        ]
    )

    yield res, subnet_label
