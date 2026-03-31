import ipaddress
import json
import re

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
)

# Lists of valid regions where NodeBalancers of type "premium" or "premium_40gb" can be created
PREMIUM_REGIONS = [
    "nl-ams",
    "jp-tyo-3",
    "sg-sin-2",
    "de-fra-2",
    "in-bom-2",
    "gb-lon",
    "us-lax",
    "id-cgk",
    "us-mia",
    "it-mil",
    "jp-osa",
    "in-maa",
    "se-sto",
    "br-gru",
    "us-sea",
    "fr-par",
    "us-iad",
    "pl-labkrk-2",  # DevCloud
]
PREMIUM_40GB_REGIONS = ["us-iad"]  # No DevCloud region for premium_40gb type


def nodebalancer_created():
    return "[0-9]+,balancer[0-9]+,us-ord,[0-9]+-[0-9]+-[0-9]+-[0-9]+.ip.linodeusercontent.com,0"


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


def test_nb_with_backend_vpc_only(get_vpc_with_subnet):
    vpc = get_vpc_with_subnet

    nb_attrs = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "create",
            "--region",
            vpc["region"],
            "--backend_vpcs.subnet_id",
            str(vpc["subnets"][0]["id"]),
            "--json",
        ]
    )
    nb_attrs = json.loads(nb_attrs)
    nb_id = str(nb_attrs[0]["id"])
    assert isinstance(ipaddress.ip_address(nb_attrs[0]["ipv4"]), ipaddress.IPv4Address)
    assert isinstance(ipaddress.ip_address(nb_attrs[0]["ipv6"]), ipaddress.IPv6Address)
    assert nb_attrs[0]["frontend_address_type"] == "public"
    assert nb_attrs[0]["frontend_vpc_subnet_id"] is None

    nb_vpcs = exec_test_command(
        BASE_CMDS["nodebalancers"] + ["vpcs-list", nb_id, "--json",]
    )
    nb_vpcs = json.loads(nb_vpcs)
    assert len(nb_vpcs) == 1
    assert nb_vpcs[0]["purpose"] == "backend"

    nb_vpc = exec_test_command(
        BASE_CMDS["nodebalancers"] + ["vpc-view", nb_id, str(nb_vpcs[0]["id"]), "--json",]
    )
    nb_vpc = json.loads(nb_vpc)
    assert nb_vpc[0]["purpose"] == "backend"

    # TODO: Uncomment when API implementation of /backend_vpcs and /frontend_vpcs endpoints is finished
    # nb_backend_vpcs = exec_test_command(
    #     BASE_CMDS["nodebalancers"] + ["backend_vpcs-list", nb_id, "--json",]
    # )
    # nb_backend_vpcs = json.loads(nb_backend_vpcs)
    # assert len(nb_backend_vpcs) == 1
    # assert nb_backend_vpcs[0]["purpose"] == "backend"
    #
    # nb_frontend_vpcs = exec_test_command(
    #     BASE_CMDS["nodebalancers"] + ["frontend_vpcs-list", nb_id, "--json",]
    # )
    # nb_frontend_vpcs = json.loads(nb_frontend_vpcs)
    # assert len(nb_frontend_vpcs) == 0

    delete_target_id(target="nodebalancers", id=nb_id)


@pytest.mark.parametrize("get_vpc_with_subnet", [PREMIUM_REGIONS], indirect=True)
def test_nb_with_frontend_ipv4_only(get_vpc_with_subnet):
    vpc = get_vpc_with_subnet
    ipv4_address = "10.0.0.2"  # first available address

    nb_attrs = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "create",
            "--region",
            vpc["region"],
            "--frontend_vpcs.subnet_id",
            str(vpc["subnets"][0]["id"]),
            "--frontend_vpcs.ipv4_range",
            "10.0.0.0/24",
            "--type",
            "premium",
            "--json",
        ]
    )
    nb_attrs = json.loads(nb_attrs)
    nb_id = str(nb_attrs[0]["id"])

    assert nb_attrs[0]["ipv4"] == ipv4_address
    assert nb_attrs[0]["ipv6"] is None
    assert nb_attrs[0]["frontend_address_type"] == "vpc"
    assert nb_attrs[0]["frontend_vpc_subnet_id"] == vpc["subnets"][0]["id"]

    # TODO: Uncomment when API implementation of /backend_vpcs and /frontend_vpcs endpoints is finished
    # nb_frontend_vpcs = exec_test_command(
    #     BASE_CMDS["nodebalancers"] + ["frontend_vpcs-list", nb_id, "--json",]
    # )
    # nb_frontend_vpcs = json.loads(nb_frontend_vpcs)
    # assert len(nb_frontend_vpcs) == 1
    # assert nb_frontend_vpcs[0]["purpose"] == "frontend"
    #
    # nb_backend_vpcs = exec_test_command(
    #     BASE_CMDS["nodebalancers"] + ["backend_vpcs-list", nb_id, "--json",]
    # )
    # nb_backend_vpcs = json.loads(nb_backend_vpcs)
    # assert len(nb_backend_vpcs) == 0

    delete_target_id(target="nodebalancers", id=nb_id)


@pytest.mark.parametrize("get_vpc_with_subnet", [PREMIUM_REGIONS], indirect=True)
def test_nb_with_frontend_ipv6_in_single_stack_vpc_fail(get_vpc_with_subnet):
    vpc = get_vpc_with_subnet

    result = exec_failing_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "create",
            "--region",
            vpc["region"],
            "--frontend_vpcs.subnet_id",
            str(vpc["subnets"][0]["id"]),
            "--frontend_vpcs.ipv6_range",
            "/62",
            "--type",
            "premium",
        ],
    )
    assert "Request failed: 400" in result
    assert "No IPv6 subnets available in VPC" in result


@pytest.mark.parametrize("get_vpc_with_subnet", [PREMIUM_REGIONS], indirect=True)
def test_nb_with_frontend_and_default_type_fail(get_vpc_with_subnet):
    vpc = get_vpc_with_subnet

    result = exec_failing_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "create",
            "--region",
            vpc["region"],
            "--frontend_vpcs.subnet_id",
            str(vpc["subnets"][0]["id"]),
        ],
    )
    assert "Request failed: 400" in result
    assert "NodeBalancer with frontend VPC IP must be premium" in result


@pytest.mark.parametrize(
    "get_vpc_with_subnet",
    [PREMIUM_40GB_REGIONS],
    indirect=True,
)
def test_nb_with_premium40gb_type(get_vpc_with_subnet):
    vpc = get_vpc_with_subnet

    nb_attrs = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "create",
            "--region",
            vpc["region"],
            "--type",
            "premium_40gb",
            "--json",
        ],
    )
    nb_attrs = json.loads(nb_attrs)
    assert nb_attrs[0]["type"] == "premium_40gb"

    delete_target_id(target="nodebalancers", id=str(nb_attrs[0]["id"]))
