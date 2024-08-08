import re
import time

from linodecli.exit_codes import ExitCodes
from tests.integration.conftest import get_regions_with_capabilities
from tests.integration.helpers import (
    exec_failing_test_command,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "vpcs"]


def test_list_vpcs(test_vpc_wo_subnet):
    vpc_id = test_vpc_wo_subnet
    res = (
        exec_test_command(BASE_CMD + ["ls", "--text"]).stdout.decode().rstrip()
    )
    headers = ["id", "label", "description", "region"]

    for header in headers:
        assert header in res
    assert vpc_id in res


def test_view_vpc(test_vpc_wo_subnet):
    vpc_id = test_vpc_wo_subnet

    res = (
        exec_test_command(BASE_CMD + ["view", vpc_id, "--text", "--no-headers"])
        .stdout.decode()
        .rstrip()
    )

    assert vpc_id in res


def test_update_vpc(test_vpc_wo_subnet):
    vpc_id = test_vpc_wo_subnet

    new_label = str(time.time_ns()) + "label"

    updated_label = (
        exec_test_command(
            BASE_CMD
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
        .stdout.decode()
        .rstrip()
    )

    description = (
        exec_test_command(
            BASE_CMD
            + ["view", vpc_id, "--text", "--no-headers", "--format=description"]
        )
        .stdout.decode()
        .rstrip()
    )

    assert new_label == updated_label
    assert "new description" in description


def test_list_subnets(test_vpc_w_subnet):
    vpc_id = test_vpc_w_subnet

    res = (
        exec_test_command(
            BASE_CMD + ["subnets-list", vpc_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )

    lines = res.splitlines()

    headers = ["id", "label", "ipv4"]

    for header in headers:
        assert header in lines[0]

    for line in lines[1:]:
        assert re.match(
            r"^(\d+),(\w+),(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d+)$", line
        ), "String format does not match"


def test_view_subnet(test_vpc_wo_subnet, test_subnet):
    # note calling test_subnet fixture will add subnet to test_vpc_wo_subnet
    res, label = test_subnet

    res = res.split(",")

    vpc_subnet_id = res[0]

    vpc_id = test_vpc_wo_subnet

    output = (
        exec_test_command(
            BASE_CMD + ["subnet-view", vpc_id, vpc_subnet_id, "--text"]
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "ipv4"]
    for header in headers:
        assert header in output
    assert vpc_subnet_id in output


def test_update_subnet(test_vpc_w_subnet):
    vpc_id = test_vpc_w_subnet

    new_label = str(time.time_ns()) + "label"

    subnet_id = (
        exec_test_command(
            BASE_CMD
            + ["subnets-list", vpc_id, "--text", "--format=id", "--no-headers"]
        )
        .stdout.decode()
        .rstrip()
    )

    updated_label = (
        exec_test_command(
            BASE_CMD
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
        .stdout.decode()
        .rstrip()
    )

    assert new_label == updated_label


def test_fails_to_create_vpc_invalid_label():
    invalid_label = "invalid_label"
    region = get_regions_with_capabilities(["VPCs"])[0]

    res = (
        exec_failing_test_command(
            BASE_CMD + ["create", "--label", invalid_label, "--region", region],
            ExitCodes.REQUEST_FAILED,
        )
        .stderr.decode()
        .rstrip()
    )

    assert "Request failed: 400" in res
    assert "Label must include only ASCII" in res


def test_fails_to_create_vpc_duplicate_label(test_vpc_wo_subnet):
    vpc_id = test_vpc_wo_subnet
    label = (
        exec_test_command(
            BASE_CMD
            + ["view", vpc_id, "--text", "--no-headers", "--format=label"]
        )
        .stdout.decode()
        .rstrip()
    )
    region = get_regions_with_capabilities(["VPCs"])[0]

    res = (
        exec_failing_test_command(
            BASE_CMD + ["create", "--label", label, "--region", region],
            ExitCodes.REQUEST_FAILED,
        )
        .stderr.decode()
        .rstrip()
    )

    assert "Label must be unique among your VPCs" in res


def test_fails_to_update_vpc_invalid_label(test_vpc_wo_subnet):
    vpc_id = test_vpc_wo_subnet
    invalid_label = "invalid_label"

    res = (
        exec_failing_test_command(
            BASE_CMD + ["update", vpc_id, "--label", invalid_label],
            ExitCodes.REQUEST_FAILED,
        )
        .stderr.decode()
        .rstrip()
    )

    assert "Request failed: 400" in res
    assert "Label must include only ASCII" in res


def test_fails_to_create_vpc_subnet_w_invalid_label(test_vpc_wo_subnet):
    vpc_id = test_vpc_wo_subnet
    invalid_label = "invalid_label"
    region = get_regions_with_capabilities(["VPCs"])[0]

    res = exec_failing_test_command(
        BASE_CMD
        + [
            "subnet-create",
            "--label",
            invalid_label,
            "--ipv4",
            "10.1.0.0/24",
            vpc_id,
        ],
        ExitCodes.REQUEST_FAILED,
    ).stderr.decode()

    assert "Request failed: 400" in res
    assert "Label must include only ASCII" in res


def test_fails_to_update_vpc_subenet_w_invalid_label(test_vpc_w_subnet):
    vpc_id = test_vpc_w_subnet

    invalid_label = "invalid_label"

    subnet_id = (
        exec_test_command(
            BASE_CMD
            + ["subnets-list", vpc_id, "--text", "--format=id", "--no-headers"]
        )
        .stdout.decode()
        .rstrip()
    )

    res = (
        exec_failing_test_command(
            BASE_CMD
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
        .stderr.decode()
        .rstrip()
    )

    assert "Request failed: 400" in res
    assert "Label must include only ASCII" in res
