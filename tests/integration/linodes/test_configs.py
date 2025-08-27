from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_test_command,
    get_random_text,
    retry_exec_test_command_with_delay,
)
from tests.integration.linodes.fixtures import (  # noqa: F401
    TEST_REGION,
    cleanup_vpc,
    config_vpc_interface,
    linode_disk_config,
    linode_instance_config_tests,
    test_vpc_w_subnet,
)
from tests.integration.linodes.helpers import (
    get_disk_ids,
)


def test_config_create(linode_instance_config_tests):
    linode_id = linode_instance_config_tests

    label = get_random_text(5) + "_config"
    disk_id = get_disk_ids(linode_id=linode_id)[1]

    result = exec_test_command(
        BASE_CMDS["linodes"]
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

    headers = ["id", "label", "kernel"]

    assert_headers_in_lines(headers, result.splitlines())
    assert label in result


def test_config_delete(linode_instance_config_tests):
    linode_id = linode_instance_config_tests

    label = get_random_text(5) + "_config"
    disk_id = get_disk_ids(linode_id=linode_id)[1]

    config_id = exec_test_command(
        BASE_CMDS["linodes"]
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

    retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"]
        + [
            "config-delete",
            linode_id,
            config_id,
        ]
    )


def test_config_update_label(linode_instance_config_tests, linode_disk_config):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config

    updated_label = get_random_text(4) + "_updatedconfig"

    res = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "config-update",
            linode_id,
            config_id,
            "--label",
            updated_label,
            "--text",
        ]
    )

    headers = ["id", "label", "kernel"]

    assert_headers_in_lines(headers, res.splitlines())
    assert updated_label in res


def test_config_view(linode_instance_config_tests, linode_disk_config):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config

    res = exec_test_command(
        BASE_CMDS["linodes"] + ["config-view", linode_id, config_id, "--text"]
    )

    headers = ["id", "label", "kernel"]

    assert_headers_in_lines(headers, res.splitlines())
    assert config_id in res


def test_configs_list(linode_instance_config_tests):
    linode_id = linode_instance_config_tests

    res = exec_test_command(
        BASE_CMDS["linodes"] + ["configs-list", linode_id, "--text"]
    )

    headers = ["id", "label", "kernel"]

    assert_headers_in_lines(headers, res.splitlines())


def test_config_interface_add_vlan(
    linode_instance_config_tests, linode_disk_config
):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config

    label = get_random_text(5) + "vlan"

    res = exec_test_command(
        BASE_CMDS["linodes"]
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

    res = exec_test_command(
        BASE_CMDS["linodes"]
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

    headers = ["id", "label", "purpose", "ipam_address"]

    assert_headers_in_lines(headers, res.splitlines())


def test_config_interface_view(
    linode_instance_config_tests, linode_disk_config, config_vpc_interface
):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config
    interface_id = config_vpc_interface

    res = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "config-interface-view",
            linode_id,
            config_id,
            interface_id,
            "--text",
        ]
    )

    headers = ["id", "label", "purpose", "ipam_address"]

    assert_headers_in_lines(headers, res.splitlines())
    assert interface_id in res


def test_config_interfaces_list(
    linode_instance_config_tests, linode_disk_config
):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config

    res = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "config-interfaces-list",
            linode_id,
            config_id,
            "--text",
        ]
    )

    headers = ["id", "label", "purpose", "ipam_address"]

    assert_headers_in_lines(headers, res.splitlines())


def config_interfaces_order(
    linode_instance_config_tests, linode_disk_config, config_vpc_interface
):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config
    interface_id = config_vpc_interface

    process = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "config-interfaces-order",
            linode_id,
            config_id,
            "--ids",
            interface_id,
        ]
    )

    assert process.returncode == 0
