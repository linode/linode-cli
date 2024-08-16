import re

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
)
from tests.integration.linodes.helpers_linodes import DEFAULT_TEST_IMAGE

BASE_CMD = ["linode-cli", "nodebalancers"]
nodebalancer_created = "[0-9]+,balancer[0-9]+,us-ord,[0-9]+-[0-9]+-[0-9]+-[0-9]+.ip.linodeusercontent.com,0"


@pytest.fixture(scope="package")
def test_node_balancers(linode_cloud_firewall):
    # create a default nodebalancer
    nodebalancer_id = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--region",
                "us-ord",
                "--firewall_id",
                linode_cloud_firewall,
                "--text",
                "--delimiter",
                ",",
                "--format",
                "id",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    # create one standard config
    config_id = (
        exec_test_command(
            BASE_CMD
            + [
                "config-create",
                nodebalancer_id,
                "--delimiter",
                ",",
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    linode_create = (
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "create",
                "--root_pass",
                "aComplex@Password",
                "--booted",
                "true",
                "--region",
                "us-ord",
                "--type",
                "g6-nanode-1",
                "--private_ip",
                "true",
                "--image",
                DEFAULT_TEST_IMAGE,
                "--firewall_id",
                linode_cloud_firewall,
                "--text",
                "--delimiter",
                ",",
                "--format",
                "id,ipv4",
                "--no-header",
                "--suppress-warnings",
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    linode_arr = linode_create.split(",")
    linode_id = linode_arr[0]
    ip_arr = linode_arr[1].split(" ")
    node_ip = ip_arr[1]
    node_label = "defaultnode1"

    node_id = (
        exec_test_command(
            BASE_CMD
            + [
                "node-create",
                "--address",
                node_ip + ":80",
                "--label",
                node_label,
                "--weight",
                "100",
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
                nodebalancer_id,
                config_id,
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield nodebalancer_id, config_id, node_id, node_ip

    delete_target_id(target="nodebalancers", id=nodebalancer_id)
    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture
def create_linode_to_add(linode_cloud_firewall):
    linode = (
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "create",
                "--root_pass",
                "aComplex@Password",
                "--booted",
                "true",
                "--region",
                "us-ord",
                "--type",
                "g6-nanode-1",
                "--private_ip",
                "true",
                "--image",
                DEFAULT_TEST_IMAGE,
                "--firewall_id",
                linode_cloud_firewall,
                "--text",
                "--delimiter",
                ",",
                "--format",
                "id,ipv4",
                "--no-header",
                "--suppress-warnings",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield linode

    linode_arr = linode.split(",")
    linode_id = linode_arr[0]
    delete_target_id("linodes", linode_id)


def test_fail_to_create_nodebalancer_without_region():
    result = exec_failing_test_command(
        BASE_CMD + ["create", "--text", "--no-headers"],
        ExitCodes.REQUEST_FAILED,
    ).stderr.decode()
    assert "Request failed: 400" in result
    assert "region	region is required" in result


@pytest.mark.smoke
def test_create_nodebalancer_with_default_conf(
    nodebalancer_with_default_conf,
):
    result = nodebalancer_with_default_conf
    assert re.search(nodebalancer_created, result)


def test_list_nodebalancers_and_status(test_node_balancers):
    result = exec_test_command(
        BASE_CMD
        + [
            "list",
            "--no-headers",
            "--text",
            "--delimiter",
            ",",
            "--format",
            "id,label,region,hostname,client_conn_throttle",
        ]
    ).stdout.decode()
    assert re.search(nodebalancer_created, result)


def test_display_public_ipv4_for_nodebalancer(test_node_balancers):
    nodebalancer_id = test_node_balancers[0]

    result = exec_test_command(
        BASE_CMD
        + [
            "view",
            nodebalancer_id,
            "--format",
            "ipv4",
            "--text",
            "--no-headers",
        ]
    ).stdout.decode()
    assert re.search(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", result)


def test_fail_to_view_nodebalancer_with_invalid_id():
    result = exec_failing_test_command(
        BASE_CMD + ["view", "535", "--text", "--no-headers"],
        ExitCodes.REQUEST_FAILED,
    ).stderr.decode()

    assert "Request failed: 404" in result


def test_create_standard_configuration_profile(test_node_balancers):
    nodebalancer_id = test_node_balancers[0]

    result = exec_test_command(
        BASE_CMD
        + [
            "config-create",
            nodebalancer_id,
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
            "--port",
            "82",
        ]
    ).stdout.decode()
    assert re.search(
        "[0-9]+,82,http,roundrobin,none,True,recommended,,", result
    )


def test_view_configuration_profile(test_node_balancers):
    nodebalancer_id = test_node_balancers[0]
    config_id = test_node_balancers[1]

    result = exec_test_command(
        BASE_CMD
        + [
            "config-view",
            nodebalancer_id,
            config_id,
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    ).stdout.decode()
    assert re.search(
        "[0-9]+,80,http,roundrobin,none,True,recommended,,", result
    )


def test_add_node_to_conf_profile(test_node_balancers, create_linode_to_add):
    linode_create = create_linode_to_add
    linode_arr = linode_create.split(",")
    ip_arr = linode_arr[1].split(" ")
    node_ip = ip_arr[1]

    node_label = "testnode1"
    nodebalancer_id = test_node_balancers[0]
    config_id = test_node_balancers[1]

    result = exec_test_command(
        BASE_CMD
        + [
            "node-create",
            "--address",
            node_ip + ":80",
            "--label",
            node_label,
            "--weight",
            "100",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            nodebalancer_id,
            config_id,
        ]
    ).stdout.decode()

    assert re.search(
        "[0-9]+," + node_label + "," + node_ip + ":80,Unknown,100,accept",
        result,
    )


def test_update_node_label(test_node_balancers):
    nodebalancer_id = test_node_balancers[0]
    config_id = test_node_balancers[1]
    node_id = test_node_balancers[2]
    node_ip = test_node_balancers[3]
    new_label = "testnode1-edited"

    result = exec_test_command(
        BASE_CMD
        + [
            "node-update",
            nodebalancer_id,
            config_id,
            node_id,
            "--label",
            new_label,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()

    assert re.search(
        "[0-9]+," + new_label + "," + node_ip + ":80" + ",Unknown,100,accept",
        result,
    )


def test_update_node_port(test_node_balancers):
    nodebalancer_id = test_node_balancers[0]
    config_id = test_node_balancers[1]
    node_id = test_node_balancers[2]
    node_ip = test_node_balancers[3]

    updated_port = ":23"

    new_address = node_ip + updated_port

    result = exec_test_command(
        BASE_CMD
        + [
            "node-update",
            nodebalancer_id,
            config_id,
            node_id,
            "--address",
            new_address,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()

    assert "[0-9]+,.," + new_address + ",Unknown,100,accept", result


def test_fail_to_update_node_to_public_ipv4_address(test_node_balancers):
    nodebalancer_id = test_node_balancers[0]
    config_id = test_node_balancers[1]
    node_id = test_node_balancers[2]

    public_ip = "8.8.8.8:80"

    result = exec_failing_test_command(
        BASE_CMD
        + [
            "node-update",
            nodebalancer_id,
            config_id,
            node_id,
            "--address",
            public_ip,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ],
        ExitCodes.REQUEST_FAILED,
    ).stderr.decode()

    assert "Request failed: 400" in result
    assert "Must begin with 192.168" in result


def test_remove_node_from_configuration_profile(test_node_balancers):
    nodebalancer_id = test_node_balancers[0]
    config_id = test_node_balancers[1]
    node_id = test_node_balancers[2]

    exec_test_command(
        BASE_CMD + ["node-delete", nodebalancer_id, config_id, node_id]
    )


def test_update_the_port_of_a_configuration_profile(test_node_balancers):
    nodebalancer_id = test_node_balancers[0]
    config_id = test_node_balancers[1]

    result = exec_test_command(
        BASE_CMD
        + [
            "config-update",
            "--port",
            "10700",
            "--protocol",
            "tcp",
            nodebalancer_id,
            config_id,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()

    assert re.search(
        "[0-9]+,10700,tcp,roundrobin,none,True,recommended,,", result
    )


def test_add_additional_configuration_profile(test_node_balancers):
    nodebalancer_id = test_node_balancers[0]

    result = exec_test_command(
        BASE_CMD
        + [
            "config-create",
            nodebalancer_id,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--port",
            "81",
        ]
    ).stdout.decode()

    assert re.search(
        "^[0-9](.*),81,http,roundrobin,none,True,recommended,,", result
    )


def test_list_multiple_configuration_profile(test_node_balancers):
    nodebalancer_id = test_node_balancers[0]

    result = exec_test_command(
        BASE_CMD
        + [
            "config-create",
            nodebalancer_id,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--port",
            "83",
        ]
    )

    result = exec_test_command(
        BASE_CMD
        + [
            "configs-list",
            nodebalancer_id,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()

    assert re.search(
        "[0-9]+,8[0-1],http,roundrobin,none,True,recommended,,", result
    )
    assert re.search(
        "[0-9]+,83,http,roundrobin,none,True,recommended,,", result
    )
