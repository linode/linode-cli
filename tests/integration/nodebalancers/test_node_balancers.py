import re

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    assert_help_parameters_list_for_command,
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
)
from tests.integration.nodebalancers.fixtures import (  # noqa: F401
    linode_to_add,
    nodebalancer_premium_with_backend_vpc,
    nodebalancer_w_config_and_node,
    nodebalancer_with_default_conf,
    nodebalancer_with_reserved_ipv4,
    nodebalancer_with_udp_config_and_node,
    simple_nodebalancer_with_config,
    vpc_for_nb_premium_backend_connectivity,
)


def test_fail_to_create_nodebalancer_without_region():
    result = exec_failing_test_command(
        BASE_CMDS["nodebalancers"]
        + ["create", "--text", "--no-headers", "--no-defaults"],
        ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 400" in result
    assert "region	region is required" in result


@pytest.mark.smoke
def test_create_nodebalancer_with_default_conf(
    nodebalancer_with_default_conf,
):
    result = nodebalancer_with_default_conf
    assert re.search(nodebalancer_created(), result)


def test_list_nodebalancers_and_status(nodebalancer_w_config_and_node):
    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "list",
            "--no-headers",
            "--text",
            "--delimiter",
            ",",
            "--format",
            "id,label,region,hostname,client_conn_throttle",
        ]
    )
    assert re.search(nodebalancer_created(), result)


def test_verify_columns_for_list_nodebalancers():
    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "list",
            "--text",
            "--delimiter",
            ",",
        ]
    )
    lines = result.splitlines()
    headers = [
        "id",
        "label",
        "region",
        "type",
        "backend_connectivity",
        "backend_ipv6_prefix",
    ]
    assert_headers_in_lines(headers, lines)


def test_display_public_ipv4_for_nodebalancer(nodebalancer_w_config_and_node):
    nodebalancer_id = nodebalancer_w_config_and_node[0]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "view",
            nodebalancer_id,
            "--format",
            "ipv4",
            "--text",
            "--no-headers",
        ]
    )
    assert re.search(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", result)


def test_display_nodebalancer_with_res_ipv4(nodebalancer_with_reserved_ipv4):
    res_ip, nb_id = nodebalancer_with_reserved_ipv4
    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "view",
            nb_id,
            "--format",
            "ipv4",
            "--text",
            "--no-headers",
        ]
    )

    assert res_ip in result


def test_fail_to_view_nodebalancer_with_invalid_id():
    result = exec_failing_test_command(
        BASE_CMDS["nodebalancers"] + ["view", "535", "--text", "--no-headers"],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 404" in result


def test_create_standard_configuration_profile(nodebalancer_w_config_and_node):
    nodebalancer_id = nodebalancer_w_config_and_node[0]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
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
    )
    assert re.search(
        "[0-9]+,82,http,roundrobin,none,True,recommended,,", result
    )


def test_view_configuration_profile(nodebalancer_w_config_and_node):
    nodebalancer_id = nodebalancer_w_config_and_node[0]
    config_id = nodebalancer_w_config_and_node[1]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "config-view",
            nodebalancer_id,
            config_id,
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    )
    assert re.search(
        "[0-9]+,80,http,roundrobin,none,True,recommended,,", result
    )


def test_add_node_to_conf_profile(
    nodebalancer_w_config_and_node, linode_to_add
):
    linode_create = linode_to_add
    linode_arr = linode_create.split(",")
    ip_arr = linode_arr[1].split(" ")
    node_ip = ip_arr[1]

    node_label = "testnode1"
    nodebalancer_id = nodebalancer_w_config_and_node[0]
    config_id = nodebalancer_w_config_and_node[1]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
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
    )

    assert re.search(
        "[0-9]+," + node_label + "," + node_ip + ":80,Unknown,100,accept",
        result,
    )


def test_update_node_label(nodebalancer_w_config_and_node):
    nodebalancer_id = nodebalancer_w_config_and_node[0]
    config_id = nodebalancer_w_config_and_node[1]
    node_id = nodebalancer_w_config_and_node[2]
    node_ip = nodebalancer_w_config_and_node[3]
    new_label = "testnode1-edited"

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
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
    )

    assert re.search(
        "[0-9]+," + new_label + "," + node_ip + ":80" + ",Unknown,100,accept",
        result,
    )


def test_update_node_port(nodebalancer_w_config_and_node):
    nodebalancer_id = nodebalancer_w_config_and_node[0]
    config_id = nodebalancer_w_config_and_node[1]
    node_id = nodebalancer_w_config_and_node[2]
    node_ip = nodebalancer_w_config_and_node[3]

    updated_port = ":23"

    new_address = node_ip + updated_port

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
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
    )

    assert "[0-9]+,.," + new_address + ",Unknown,100,accept", result


def test_fail_to_update_node_to_public_ipv4_address(
    nodebalancer_w_config_and_node,
):
    nodebalancer_id = nodebalancer_w_config_and_node[0]
    config_id = nodebalancer_w_config_and_node[1]
    node_id = nodebalancer_w_config_and_node[2]

    public_ip = "8.8.8.8:80"

    result = exec_failing_test_command(
        BASE_CMDS["nodebalancers"]
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
    )

    assert "Request failed: 400" in result
    assert "Must begin with 192.168" in result


def test_remove_node_from_configuration_profile(nodebalancer_w_config_and_node):
    nodebalancer_id = nodebalancer_w_config_and_node[0]
    config_id = nodebalancer_w_config_and_node[1]
    node_id = nodebalancer_w_config_and_node[2]

    exec_test_command(
        BASE_CMDS["nodebalancers"]
        + ["node-delete", nodebalancer_id, config_id, node_id]
    )


def test_update_the_port_of_a_configuration_profile(
    nodebalancer_w_config_and_node,
):
    nodebalancer_id = nodebalancer_w_config_and_node[0]
    config_id = nodebalancer_w_config_and_node[1]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
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
    )

    assert re.search(
        "[0-9]+,10700,tcp,roundrobin,none,True,recommended,,", result
    )


def test_add_additional_configuration_profile(nodebalancer_w_config_and_node):
    nodebalancer_id = nodebalancer_w_config_and_node[0]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
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
    )

    assert re.search(
        "^[0-9](.*),81,http,roundrobin,none,True,recommended,,", result
    )


def test_list_multiple_configuration_profile(nodebalancer_w_config_and_node):
    nodebalancer_id = nodebalancer_w_config_and_node[0]

    exec_test_command(
        BASE_CMDS["nodebalancers"]
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
        BASE_CMDS["nodebalancers"]
        + [
            "configs-list",
            nodebalancer_id,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    )

    assert re.search(
        "[0-9]+,8[0-1],http,roundrobin,none,True,recommended,,", result
    )
    assert re.search(
        "[0-9]+,83,http,roundrobin,none,True,recommended,,", result
    )


def test_update_node_balancer_udp_configuration(
    simple_nodebalancer_with_config,
):
    nodebalancer_id = simple_nodebalancer_with_config[0]
    config_id = simple_nodebalancer_with_config[1]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "config-update",
            nodebalancer_id,
            config_id,
            "--port",
            "80",
            "--protocol",
            "udp",
            "--algorithm",
            "roundrobin",
            "--check_interval",
            "80",
            "--check_timeout",
            "15",
            "--check_attempts",
            "2",
            "--check_path",
            "/testUpdate",
            "--check_body",
            "OK",
            "--check_passive",
            "False",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    )
    assert result == config_id + ",80,udp,roundrobin,none,False,none,,"


def test_rebuild_node_balancer_udp_configuration(
    nodebalancer_with_udp_config_and_node,
):
    nodebalancer_id = nodebalancer_with_udp_config_and_node[0]
    config_id = nodebalancer_with_udp_config_and_node[1]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "config-rebuild",
            nodebalancer_id,
            config_id,
            "--port",
            "80",
            "--protocol",
            "udp",
            "--algorithm",
            "ring_hash",
            "--nodes.label",
            "defaultnode1",
            "--nodes.address",
            nodebalancer_with_udp_config_and_node[3] + ":80",
            "--nodes.weight",
            "50",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    )
    assert result == config_id + ",80,udp,ring_hash,session,False,none,,"


def test_list_node_balancer_configurations_with_udp_type(
    nodebalancer_with_udp_config_and_node,
):
    nodebalancer_id = nodebalancer_with_udp_config_and_node[0]
    config_id = nodebalancer_with_udp_config_and_node[1]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "configs-list",
            nodebalancer_id,
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    )
    assert result == config_id + ",80,udp,roundrobin,session,False,none,,"


def test_view_node_balancer_udp_configuration(
    nodebalancer_with_udp_config_and_node,
):
    nodebalancer_id = nodebalancer_with_udp_config_and_node[0]
    config_id = nodebalancer_with_udp_config_and_node[1]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "config-view",
            nodebalancer_id,
            config_id,
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    )
    assert result == config_id + ",80,udp,roundrobin,session,False,none,,"


def test_update_node_for_node_balancer_udp_configuration(
    nodebalancer_with_udp_config_and_node,
):
    nodebalancer_id = nodebalancer_with_udp_config_and_node[0]
    config_id = nodebalancer_with_udp_config_and_node[1]
    node_id = nodebalancer_with_udp_config_and_node[2]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "node-update",
            nodebalancer_id,
            config_id,
            node_id,
            "--weight",
            "30",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    )
    assert (
        result
        == node_id
        + ",defaultnode1,"
        + nodebalancer_with_udp_config_and_node[3]
        + ":80,Unknown,30,none,"
    )


def test_list_nodes_for_node_balancer_udp_configuration(
    nodebalancer_with_udp_config_and_node,
):
    nodebalancer_id = nodebalancer_with_udp_config_and_node[0]
    config_id = nodebalancer_with_udp_config_and_node[1]
    node_id = nodebalancer_with_udp_config_and_node[2]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "nodes-list",
            nodebalancer_id,
            config_id,
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    )

    assert (
        result
        == node_id
        + ",defaultnode1,"
        + nodebalancer_with_udp_config_and_node[3]
        + ":80,Unknown,100,none,"
    )


def test_view_node_for_node_balancer_udp_configuration(
    nodebalancer_with_udp_config_and_node,
):
    nodebalancer_id = nodebalancer_with_udp_config_and_node[0]
    config_id = nodebalancer_with_udp_config_and_node[1]
    node_id = nodebalancer_with_udp_config_and_node[2]

    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "node-view",
            nodebalancer_id,
            config_id,
            node_id,
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    )
    assert (
        result
        == node_id
        + ",defaultnode1,"
        + nodebalancer_with_udp_config_and_node[3]
        + ":80,Unknown,100,none,"
    )


def nodebalancer_created():
    return "[0-9]+,balancer[0-9]+,us-ord,[0-9]+-[0-9]+-[0-9]+-[0-9]+.ip.linodeusercontent.com,0"


def test_premium_nodebalancer_with_vpc_backend_connectivity(
    nodebalancer_premium_with_backend_vpc,
):
    result_create = nodebalancer_premium_with_backend_vpc[1]
    assert "premium" in result_create
    assert "vpc" in result_create
    assert "/96" in result_create

    result_view = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "view",
            nodebalancer_premium_with_backend_vpc[0],
            "--text",
            "--no-headers",
            "--format",
            "type,backend_connectivity,backend_ipv6_prefix",
            "--delimiter",
            ",",
        ]
    ).split(",")
    assert result_view[0] == "premium"
    assert result_view[1] == "vpc"
    assert result_view[2].endswith("/96")

    result_update = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "update",
            nodebalancer_premium_with_backend_vpc[0],
            "--label",
            "update_label_" + get_random_text(5),
            "--client_conn_throttle",
            "0",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    )
    assert "premium" in result_update
    assert "vpc" in result_update
    assert "/96" in result_update


def test_create_nodebalancer_help_command():
    output = exec_test_command(
        BASE_CMDS["nodebalancers"] + ["create", "--help", "--text"]
    )
    available_arguments = [
        "backend_connectivity",
        "client_conn_throttle",
        "configs",
        "firewall_id",
        "ipv4",
        "region",
        "type",
        "vpcs.ipv4_range",
        "vpcs.ipv4_range_auto_assign",
        "vpcs.subnet_id",
    ]
    assert_help_parameters_list_for_command(available_arguments, output)
