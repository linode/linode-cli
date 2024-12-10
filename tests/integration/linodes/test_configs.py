import json
import time

import pytest

from tests.integration.conftest import create_vpc_w_subnet
from tests.integration.helpers import (
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
    retry_exec_test_command_with_delay,
)
from tests.integration.linodes.helpers_linodes import (
    BASE_CMD,
    create_linode,
    get_disk_ids,
)

TEST_REGION = get_random_region_with_caps(
    required_capabilities=["Linodes", "VPCs"]
)


@pytest.fixture(scope="session", autouse=True)
def linode_instance_config_tests(linode_cloud_firewall):
    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        disk_encryption=False,
        test_region=TEST_REGION,
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="session", autouse=True)
def linode_disk_config(linode_instance_config_tests):
    linode_id = linode_instance_config_tests

    label = get_random_text(5) + "_config"
    disk_id = get_disk_ids(linode_id=linode_id)[1]

    config_id = (
        exec_test_command(
            BASE_CMD
            + [
                "config-create",
                linode_id,
                "--label",
                label,
                "--devices.sda.disk_id",
                disk_id,
                "--no-headers",
                "--format=id",
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield config_id


@pytest.fixture(scope="session", autouse=True)
def test_vpc_w_subnet(request):
    vpc_json = create_vpc_w_subnet()
    vpc_id = str(vpc_json["id"])

    yield vpc_id


@pytest.fixture(scope="session", autouse=True)
def cleanup_vpc(request, test_vpc_w_subnet):
    # Register finalizer to delete VPC after the entire session, with a delay
    def delayed_cleanup():
        time.sleep(5)  # Delay if necessary
        delete_target_id(target="vpcs", id=test_vpc_w_subnet)

    request.addfinalizer(delayed_cleanup)


@pytest.fixture(scope="session", autouse=True)
def config_vpc_interface(
    linode_instance_config_tests, linode_disk_config, test_vpc_w_subnet
):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config
    subnet_id = get_subnet_id(vpc_id=test_vpc_w_subnet)

    interface_id = (
        exec_test_command(
            BASE_CMD
            + [
                "config-interface-add",
                linode_id,
                config_id,
                "--purpose",
                "vpc",
                "--primary",
                "false",
                "--subnet_id",
                subnet_id,
                "--ipv4.vpc",
                "10.0.0.3",
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield interface_id

    retry_exec_test_command_with_delay(
        BASE_CMD
        + [
            "config-interface-delete",
            linode_id,
            config_id,
            interface_id,
        ]
    )


def create_vpc_w_subnet():
    vpc_label = get_random_text(5) + "vpc"
    subnet_label = get_random_text(5) + "subnet"

    vpc_json = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "vpcs",
                "create",
                "--label",
                vpc_label,
                "--region",
                TEST_REGION,
                "--subnets.ipv4",
                "10.0.0.0/24",
                "--subnets.label",
                subnet_label,
                "--json",
                "--suppress-warnings",
            ]
        )
        .stdout.decode()
        .rstrip()
    )[0]

    return vpc_json


def get_subnet_id(vpc_id):
    subnet_id = (
        exec_test_command(
            [
                "linode-cli",
                "vpcs",
                "subnets-list",
                vpc_id,
                "--text",
                "--format=id",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    return subnet_id


def test_config_create(linode_instance_config_tests):
    linode_id = linode_instance_config_tests

    label = get_random_text(5) + "_config"
    disk_id = get_disk_ids(linode_id=linode_id)[1]

    result = (
        exec_test_command(
            BASE_CMD
            + [
                "config-create",
                linode_id,
                "--label",
                label,
                "--devices.sda.disk_id",
                disk_id,
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "kernel"]

    assert_headers_in_lines(headers, result.splitlines())
    assert label in result


def test_config_delete(linode_instance_config_tests):
    linode_id = linode_instance_config_tests

    label = get_random_text(5) + "_config"
    disk_id = get_disk_ids(linode_id=linode_id)[1]

    config_id = (
        exec_test_command(
            BASE_CMD
            + [
                "config-create",
                linode_id,
                "--label",
                label,
                "--devices.sda.disk_id",
                disk_id,
                "--no-headers",
                "--format=id",
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    res = retry_exec_test_command_with_delay(
        BASE_CMD
        + [
            "config-delete",
            linode_id,
            config_id,
        ]
    )

    assert res.returncode == 0


def test_config_update_label(linode_instance_config_tests, linode_disk_config):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config

    updated_label = get_random_text(4) + "_updatedconfig"

    res = (
        exec_test_command(
            BASE_CMD
            + [
                "config-update",
                linode_id,
                config_id,
                "--label",
                updated_label,
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "kernel"]

    assert_headers_in_lines(headers, res.splitlines())
    assert updated_label in res


def test_config_view(linode_instance_config_tests, linode_disk_config):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config

    res = (
        exec_test_command(
            BASE_CMD + ["config-view", linode_id, config_id, "--text"]
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "kernel"]

    assert_headers_in_lines(headers, res.splitlines())
    assert config_id in res


def test_configs_list(linode_instance_config_tests):
    linode_id = linode_instance_config_tests

    res = (
        exec_test_command(BASE_CMD + ["configs-list", linode_id, "--text"])
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "kernel"]

    assert_headers_in_lines(headers, res.splitlines())


def test_config_interface_add_vlan(
    linode_instance_config_tests, linode_disk_config
):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config

    label = get_random_text(5) + "vlan"

    res = (
        exec_test_command(
            BASE_CMD
            + [
                "config-interface-add",
                linode_id,
                config_id,
                "--purpose",
                "vlan",
                "--primary",
                "false",
                "--label",
                label,
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "purpose", "ipam_address"]

    assert_headers_in_lines(headers, res.splitlines())
    assert label in res
    assert "vlan" in res


def test_config_interface_update(
    linode_instance_config_tests, linode_disk_config, config_vpc_interface
):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config
    interface_id = config_vpc_interface

    res = (
        exec_test_command(
            BASE_CMD
            + [
                "config-interface-update",
                linode_id,
                config_id,
                interface_id,
                "--ipv4.vpc",
                "10.0.0.5",
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "purpose", "ipam_address"]

    assert_headers_in_lines(headers, res.splitlines())


def test_config_interface_view(
    linode_instance_config_tests, linode_disk_config, config_vpc_interface
):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config
    interface_id = config_vpc_interface

    res = (
        exec_test_command(
            BASE_CMD
            + [
                "config-interface-view",
                linode_id,
                config_id,
                interface_id,
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "purpose", "ipam_address"]

    assert_headers_in_lines(headers, res.splitlines())
    assert interface_id in res


def test_config_interfaces_list(
    linode_instance_config_tests, linode_disk_config
):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config

    res = (
        exec_test_command(
            BASE_CMD
            + [
                "config-interfaces-list",
                linode_id,
                config_id,
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "label", "purpose", "ipam_address"]

    assert_headers_in_lines(headers, res.splitlines())


def config_interfaces_order(
    linode_instance_config_tests, linode_disk_config, config_vpc_interface
):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config
    interface_id = config_vpc_interface

    process = (
        exec_test_command(
            BASE_CMD
            + [
                "config-interfaces-order",
                linode_id,
                config_id,
                "--ids",
                interface_id,
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert process.returncode == 0
