import json
import os
import re

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    exec_failing_test_command,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
    wait_for_condition,
)

HEADERS_VPC = ["id", "label", "description", "region", "vpc_type"]
HEADERS_SUBNET = ["id", "label", "ipv4", "vpc_type"]


# TODO: Remove this variable and @pytest.mark.skipif once VPC Dual Stack is ready to ship
disable_vpc_dual_stack_tests = True


def get_vpcs_list(params: str = None):
    params = params.split() if params else []
    command = BASE_CMDS["vpcs"] + ["ls", "--text"] + params
    return exec_test_command(command)


def get_vpc_view(vpc_id: int = None):
    return json.loads(
        exec_test_command(BASE_CMDS["vpcs"] + ["view", vpc_id, "--json"])
    )[0]


def get_subnets_list(vpc_id: int, params: str = None):
    params = params.split() if params else []
    command = BASE_CMDS["vpcs"] + ["subnets-list", vpc_id] + params
    return exec_test_command(command)


def get_subnet_view(vpc_id: int, subnet_id: int):
    return json.loads(
        exec_test_command(
            BASE_CMDS["vpcs"] + ["subnet-view", vpc_id, subnet_id, "--json"]
        )
    )[0]


def test_list_vpcs(get_test_vpc_wo_subnet):
    vpc_id = get_test_vpc_wo_subnet
    output = get_vpcs_list("--page-size 100")

    assert all(header in output for header in HEADERS_VPC)
    assert vpc_id in output


def test_view_vpc(get_test_vpc_wo_subnet):
    vpc_id = get_test_vpc_wo_subnet
    output = get_vpc_view(vpc_id)

    assert all([header in output.keys() for header in HEADERS_VPC])
    assert str(output["id"]) == vpc_id
    assert output["vpc_type"] == "regular"


@pytest.mark.smoke
def test_update_vpc(get_test_vpc_wo_subnet):
    vpc_id = get_test_vpc_wo_subnet

    new_label = get_random_text(5) + "label"

    updated_label = exec_test_command(
        BASE_CMDS["vpcs"]
        + [
            "update",
            vpc_id,
            "--label",
            new_label,
            "--description",
            "new description",
            "--text",
            "--no-headers",
            "--format=label",
        ]
    )

    description = exec_test_command(
        BASE_CMDS["vpcs"]
        + ["view", vpc_id, "--text", "--no-headers", "--format=description"]
    )

    assert new_label == updated_label
    assert "new description" in description


def test_vpc_with_rdma_type(get_test_vpc_w_rdma_type):
    vpc_id = get_test_vpc_w_rdma_type

    output = get_vpcs_list("--page-size 100")
    assert all(header in output for header in HEADERS_VPC)
    assert vpc_id in output

    output = get_vpcs_list("--page-size 100 --format=vpc_type --no-headers")
    assert any(["rdma" in output.split()])

    output = get_vpc_view(vpc_id)
    assert str(output["id"]) == vpc_id
    assert output["vpc_type"] == "rdma"


def test_list_subnets(get_test_vpc_w_subnet):
    vpc_id = get_test_vpc_w_subnet

    output = get_subnets_list(vpc_id, "--text --delimiter=,").splitlines()
    assert all(header in output[0] for header in HEADERS_SUBNET)

    for line in output[1:]:
        assert re.match(
            r"^(\d+),(\w+),(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d+),(\w+)$",
            line,
        ), "String format does not match"


def test_view_subnet(get_test_subnet):
    vpc_id, subnet_id = get_test_subnet
    output = get_subnet_view(vpc_id, subnet_id)

    assert all(header in output.keys() for header in HEADERS_SUBNET)
    assert str(output["id"]) == subnet_id
    assert output["vpc_type"] == "regular"


@pytest.mark.smoke
def test_update_subnet(get_test_vpc_w_subnet):
    vpc_id = get_test_vpc_w_subnet

    new_label = get_random_text(5) + "label"

    subnet_id = exec_test_command(
        BASE_CMDS["vpcs"]
        + ["subnets-list", vpc_id, "--text", "--format=id", "--no-headers"]
    )

    updated_label = exec_test_command(
        BASE_CMDS["vpcs"]
        + [
            "subnet-update",
            vpc_id,
            subnet_id,
            "--label",
            new_label,
            "--text",
            "--format=label",
            "--no-headers",
        ]
    )

    assert new_label == updated_label


def test_subnet_with_rdma_type_vpc(get_test_subnet_w_rdma_type):
    vpc_id, subnet_id = get_test_subnet_w_rdma_type

    output = get_subnets_list(vpc_id)
    assert all(header in output for header in HEADERS_SUBNET)
    assert subnet_id in output

    output = get_subnets_list(vpc_id, "--format=vpc_type --no-headers")
    assert any(["rdma" in output.split()])

    output = get_subnet_view(vpc_id, subnet_id)
    assert str(output["id"]) == subnet_id
    assert output["vpc_type"] == "rdma"


@pytest.mark.skip(reason="Defect: ARB-8019")
def test_fails_to_create_vpc_invalid_label():
    invalid_label = "invalid_label"
    region = get_random_region_with_caps(required_capabilities=["VPCs"])

    res = exec_failing_test_command(
        BASE_CMDS["vpcs"]
        + ["create", "--label", invalid_label, "--region", region],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 400" in res
    assert "Must only use ASCII letters, numbers, and dashes" in res


def test_fails_to_create_vpc_duplicate_label(get_test_vpc_wo_subnet):
    vpc_id = get_test_vpc_wo_subnet
    label = exec_test_command(
        BASE_CMDS["vpcs"]
        + ["view", vpc_id, "--text", "--no-headers", "--format=label"]
    )
    region = get_random_region_with_caps(required_capabilities=["VPCs"])

    res = exec_failing_test_command(
        BASE_CMDS["vpcs"] + ["create", "--label", label, "--region", region],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Label must be unique among your VPCs" in res


@pytest.mark.skip(reason="Defect: ARB-8019")
def test_fails_to_update_vpc_invalid_label(get_test_vpc_wo_subnet):
    vpc_id = get_test_vpc_wo_subnet
    invalid_label = "invalid_label"

    res = exec_failing_test_command(
        BASE_CMDS["vpcs"] + ["update", vpc_id, "--label", invalid_label],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 400" in res
    assert "Must only use ASCII letters, numbers, and dashes" in res


@pytest.mark.skip(reason="Defect: ARB-8019")
def test_fails_to_create_vpc_subnet_w_invalid_label(get_test_vpc_wo_subnet):
    vpc_id = get_test_vpc_wo_subnet
    invalid_label = "invalid_label"

    res = exec_failing_test_command(
        BASE_CMDS["vpcs"]
        + [
            "subnet-create",
            "--label",
            invalid_label,
            "--ipv4",
            "10.1.0.0/24",
            vpc_id,
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 400" in res
    assert "Must only use ASCII letters, numbers, and dashes" in res


@pytest.mark.skip(reason="Defect: ARB-8019")
def test_fails_to_update_vpc_subnet_w_invalid_label(get_test_vpc_w_subnet):
    vpc_id = get_test_vpc_w_subnet

    invalid_label = "invalid_label"

    subnet_id = exec_test_command(
        BASE_CMDS["vpcs"]
        + ["subnets-list", vpc_id, "--text", "--format=id", "--no-headers"]
    )

    res = exec_failing_test_command(
        BASE_CMDS["vpcs"]
        + [
            "subnet-update",
            vpc_id,
            subnet_id,
            "--label",
            invalid_label,
            "--text",
            "--format=label",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 400" in res
    assert "Must only use ASCII letters, numbers, and dashes" in res


@pytest.mark.skipif(
    disable_vpc_dual_stack_tests, reason="Dual-stack tests disabled"
)
def test_create_vpc_with_ipv6_auto():
    region = get_random_region_with_caps(required_capabilities=["VPCs"])
    label = get_random_text(5) + "-vpc"

    res = exec_test_command(
        BASE_CMDS["vpcs"]
        + [
            "create",
            "--label",
            label,
            "--region",
            region,
            "--ipv6.range",
            "auto",
            "--json",
        ]
    )

    vpc_data = json.loads(res)[0]

    assert "id" in vpc_data
    assert "ipv6" in vpc_data
    assert isinstance(vpc_data["ipv6"], list)
    assert len(vpc_data["ipv6"]) > 0

    ipv6_entry = vpc_data["ipv6"][0]
    assert "range" in ipv6_entry


@pytest.mark.parametrize("prefix_len", ["52"])
@pytest.mark.skipif(
    disable_vpc_dual_stack_tests, reason="Dual-stack tests disabled"
)
def test_create_vpc_with_custom_ipv6_prefix_length(prefix_len):
    region = get_random_region_with_caps(required_capabilities=["VPCs"])
    label = get_random_text(5) + f"-vpc{prefix_len}"

    res = exec_test_command(
        BASE_CMDS["vpcs"]
        + [
            "create",
            "--label",
            label,
            "--region",
            region,
            "--ipv6.range",
            f"/{prefix_len}",
            "--json",
        ]
    )

    vpc_data = json.loads(res)[0]

    assert "ipv6" in vpc_data
    ipv6_entry = vpc_data["ipv6"][0]
    ipv6_range = ipv6_entry.get("range", "")
    assert isinstance(ipv6_range, str)
    assert ipv6_range.endswith(f"/{prefix_len}")


@pytest.mark.skipif(
    disable_vpc_dual_stack_tests, reason="Dual-stack tests disabled"
)
def test_create_subnet_with_ipv6_auto(get_test_vpc_wo_subnet):
    vpc_id = get_test_vpc_wo_subnet
    subnet_label = get_random_text(5) + "-ipv6subnet"

    res = exec_test_command(
        BASE_CMDS["vpcs"]
        + [
            "subnet-create",
            "--label",
            subnet_label,
            "--ipv4",
            "10.0.10.0/24",
            "--ipv6.range",
            "auto",
            vpc_id,
            "--json",
        ]
    )

    subnet_data = json.loads(res)[0]

    assert "id" in subnet_data
    assert (
        "ipv6" in subnet_data
    ), f"No IPv6 info found in response: {subnet_data}"

    ipv6_entries = subnet_data["ipv6"]
    assert (
        isinstance(ipv6_entries, list) and len(ipv6_entries) > 0
    ), "Expected non-empty IPv6 list"

    ipv6_range = ipv6_entries[0].get("range", "")
    assert isinstance(ipv6_range, str)
    assert "/" in ipv6_range, f"Unexpected IPv6 CIDR format: {ipv6_range}"


@pytest.mark.skipif(
    disable_vpc_dual_stack_tests, reason="Dual-stack tests disabled"
)
def test_fails_to_create_vpc_with_invalid_ipv6_range():
    region = get_random_region_with_caps(required_capabilities=["VPCs"])
    label = get_random_text(5) + "-invalidvpc"

    res = exec_failing_test_command(
        BASE_CMDS["vpcs"]
        + [
            "create",
            "--label",
            label,
            "--region",
            region,
            "--ipv6.range",
            "10.0.0.0/64",
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 400" in res


def test_list_vpc_ip_address():

    res = exec_test_command(
        BASE_CMDS["vpcs"] + ["ips-all-list", "--text", "--delimiter=,"]
    )

    lines = res.splitlines()

    headers = ["address", "region", "subnet_id"]

    for header in headers:
        assert header in lines[0]


@pytest.mark.skipif(
    disable_vpc_dual_stack_tests, reason="Dual-stack tests disabled"
)
def test_list_vpc_ipv6s_address():

    res = exec_test_command(
        BASE_CMDS["vpcs"] + ["ipv6s-all-list", "--text", "--delimiter=,"]
    )

    lines = res.splitlines()

    headers = ["address", "region", "subnet_id"]

    for header in headers:
        assert header in lines[0]


@pytest.mark.skipif(
    os.environ.get("LINODE_CLI_API_VERSION", None) != "v4beta",
    reason="At the moment default-ranges-all-list command is available on beta env only",
)
def test_get_vpc_default_ranges():
    headers = ["default_ipv4_ranges", "forbidden_ipv4_ranges"]

    result = json.loads(
        exec_test_command(
            BASE_CMDS["vpcs"] + ["default-ranges-all-list", "--json"]
        )
    )[0]

    assert all(header in result.keys() for header in headers)
    assert isinstance(result[headers[0]], list)
    assert isinstance(result[headers[1]], list)


@pytest.mark.parametrize(
    "create_vpc_with_ipv4, expected",
    [
        ("--ipv4.range 10.0.0.0/8", 1),
        ("--ipv4.range 10.0.0.0/8 --ipv4.range 192.168.0.0/17", 2),
    ],
    indirect=["create_vpc_with_ipv4"],
)
def test_vpc_with_ipv4(create_vpc_with_ipv4, expected):
    vpc_id = create_vpc_with_ipv4

    def vpc_ready():
        vpc_ids = exec_test_command(
            BASE_CMDS["vpcs"]
            + ["list", "--text", "--format=id", "--no-headers"]
        ).splitlines()

        return vpc_id in vpc_ids

    wait_for_condition(3, 30, vpc_ready)

    result = json.loads(
        exec_test_command(BASE_CMDS["vpcs"] + ["view", vpc_id, "--json"])
    )[0]
    assert len(result["ipv4"]) == expected


@pytest.mark.parametrize(
    "create_vpc_with_ipv4, updated",
    [
        ("--ipv4.range 10.0.0.0/8", "192.168.0.0/17"),
    ],
    indirect=["create_vpc_with_ipv4"],
)
def test_vpc_update_with_ipv4(create_vpc_with_ipv4, updated):
    vpc_id = create_vpc_with_ipv4

    exec_test_command(
        BASE_CMDS["vpcs"]
        + [
            "update",
            vpc_id,
            "--ipv4.range",
            updated,
        ]
    )

    result = json.loads(
        exec_test_command(BASE_CMDS["vpcs"] + ["view", vpc_id, "--json"])
    )[0]
    assert len(result["ipv4"]) == 1
    assert result["ipv4"][0]["range"] == updated


@pytest.mark.skipif(
    os.environ.get("LINODE_CLI_API_VERSION", None) != "v4beta",
    reason="At the moment default-ranges-all-list command is available on beta env only",
)
def test_vpc_with_forbidden_ipv4_fail():
    forbidden_ipv4 = exec_test_command(
        BASE_CMDS["vpcs"]
        + [
            "default-ranges-all-list",
            "--text",
            "--no-headers",
            "--format=forbidden_ipv4_ranges",
        ]
    ).split()[0]

    region = get_random_region_with_caps(
        required_capabilities=["VPCs", "Custom VPC IPv4 Ranges"]
    )
    label = get_random_text(5) + "-label"

    result = exec_failing_test_command(
        BASE_CMDS["vpcs"]
        + [
            "create",
            "--label",
            label,
            "--region",
            region,
            "--ipv4.range",
            forbidden_ipv4,
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 400" in result
    assert (
        f"The IPv4 range {forbidden_ipv4} overlaps with the forbidden IPv4 range {forbidden_ipv4}"
        in result
    )
