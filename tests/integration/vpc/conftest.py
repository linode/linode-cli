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
def get_test_vpc_w_subnet():
    vpc_json = create_vpc_w_subnet()
    vpc_id = str(vpc_json["id"])

    yield vpc_id

    delete_target_id(target="vpcs", id=vpc_id)


@pytest.fixture
def get_test_vpc_wo_subnet():
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
            # "--ipv6.range",    TODO: Uncomment after VPC Dual Stack is ready to ship
            # "auto",
            "--no-headers",
            "--text",
            "--format=id",
        ]
    )

    yield vpc_id

    delete_target_id(target="vpcs", id=vpc_id)


@pytest.fixture
def get_test_vpc_w_rdma_type():
    # GPUDirect RDMA capability not available for now
    # region = get_random_region_with_caps(required_capabilities=["VPCs", "GPUDirect RDMA"])
    region = get_random_region_with_caps(required_capabilities=["VPCs"])
    label = get_random_text(5) + "-test-rdma-vpc"

    vpc_id = exec_test_command(
        BASE_CMDS["vpcs"]
        + [
            "create",
            "--label",
            label,
            "--region",
            region,
            "--vpc_type",
            "rdma",
            "--no-headers",
            "--text",
            "--format=id",
        ]
    )

    yield vpc_id

    delete_target_id(target="vpcs", id=vpc_id)


@pytest.fixture
def get_test_subnet(get_test_vpc_wo_subnet):
    vpc_id = get_test_vpc_wo_subnet
    label = get_random_text(5) + "-label"
    subnet_id = exec_test_command(
        BASE_CMDS["vpcs"]
        + [
            "subnet-create",
            "--label",
            label,
            "--ipv4",
            "10.0.0.0/24",
            vpc_id,
            "--text",
            "--no-headers",
            "--delimiter=,",
        ]
    ).split(",")[0]

    yield vpc_id, subnet_id


@pytest.fixture
def get_test_subnet_w_rdma_type(get_test_vpc_w_rdma_type):
    vpc_id = get_test_vpc_w_rdma_type
    label = get_random_text(5) + "-test-rdma-subnet"
    subnet_id = exec_test_command(
        BASE_CMDS["vpcs"]
        + [
            "subnet-create",
            "--label",
            label,
            "--ipv4",
            "10.0.0.0/24",
            vpc_id,
            "--text",
            "--no-headers",
            "--delimiter=,",
        ]
    ).split(",")[0]

    yield vpc_id, subnet_id


@pytest.fixture
def create_vpc_with_ipv4(request):
    params = getattr(request, "param", None)
    params = params.split() if params else []
    region = get_random_region_with_caps(
        required_capabilities=["VPCs", "Custom VPC IPv4 Ranges"]
    )
    label = get_random_text(5) + "-label"

    vpc_id = exec_test_command(
        BASE_CMDS["vpcs"]
        + ["create", "--label", label, "--region", region]
        + params
        + ["--no-headers", "--text", "--format=id"]
    )

    yield vpc_id

    delete_target_id(target="vpcs", id=vpc_id)
