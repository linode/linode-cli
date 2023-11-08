import pytest

from tests.integration.conftest import get_regions_with_capabilities
from tests.integration.helpers import delete_target_id, exec_test_command


@pytest.fixture
def test_vpc_w_subnet():
    region = get_regions_with_capabilities(["VPCs"])[0]

    vpc_label = str(time.time_ns()) + "label"

    subnet_label = str(time.time_ns()) + "label"

    vpc_id = (
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
                "--no-headers",
                "--text",
                "--format=id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield vpc_id

    delete_target_id(target="vpcs", id=vpc_id)


@pytest.fixture
def test_subnet(test_vpc_wo_subnet):
    vpc_id = test_vpc_wo_subnet
    subnet_label = str(time.time_ns()) + "label"
    res = (
        exec_test_command(
            [
                "linode-cli",
                "vpcs",
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
        .stdout.decode()
        .rstrip()
    )

    yield res, subnet_label
