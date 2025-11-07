import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
)
from tests.integration.linodes.helpers import DEFAULT_TEST_IMAGE


@pytest.fixture(scope="package")
def nodebalancer_w_config_and_node(linode_cloud_firewall):
    # create a default nodebalancer
    nodebalancer_id = exec_test_command(
        BASE_CMDS["nodebalancers"]
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
    # create one standard config
    config_id = exec_test_command(
        BASE_CMDS["nodebalancers"]
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

    linode_create = exec_test_command(
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
    linode_arr = linode_create.split(",")
    linode_id = linode_arr[0]
    ip_arr = linode_arr[1].split(" ")
    node_ip = ip_arr[1]
    node_label = "defaultnode1"

    node_id = exec_test_command(
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
            "--format",
            "id",
        ]
    )

    yield nodebalancer_id, config_id, node_id, node_ip

    delete_target_id(target="nodebalancers", id=nodebalancer_id)
    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="module")
def linode_to_add(linode_cloud_firewall):
    linode = exec_test_command(
        BASE_CMDS["linodes"]
        + [
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

    yield linode

    linode_arr = linode.split(",")
    linode_id = linode_arr[0]
    delete_target_id("linodes", linode_id)


@pytest.fixture(scope="module")
def nodebalancer_with_default_conf(linode_cloud_firewall):
    result = exec_test_command(
        BASE_CMDS["nodebalancers"]
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
            "id,label,region,hostname,client_conn_throttle",
            "--suppress-warnings",
            "--no-headers",
        ]
    )

    yield result

    res_arr = result.split(",")
    nodebalancer_id = res_arr[0]
    delete_target_id(target="nodebalancers", id=nodebalancer_id)


@pytest.fixture(scope="function")
def nodebalancer_with_udp_config_and_node(linode_cloud_firewall):
    nodebalancer_id = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "create",
            "--region",
            "us-ord",
            "--client_conn_throttle",
            "20",
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
    config_id = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "config-create",
            nodebalancer_id,
            "--port",
            "80",
            "--protocol",
            "udp",
            "--algorithm",
            "roundrobin",
            "--check_interval",
            "90",
            "--check_timeout",
            "10",
            "--check_attempts",
            "3",
            "--check_path",
            "/test",
            "--check_body",
            "it works",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
            "--format",
            "id",
        ]
    )

    linode_create = exec_test_command(
        BASE_CMDS["linodes"]
        + [
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
    linode_arr = linode_create.split(",")
    linode_id = linode_arr[0]
    ip_arr = linode_arr[1].split(" ")
    node_ip = ip_arr[1]
    node_label = "defaultnode1"
    node_id = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "node-create",
            nodebalancer_id,
            config_id,
            "--address",
            node_ip + ":80",
            "--label",
            node_label,
            "--weight",
            "100",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
            "--format",
            "id",
        ]
    )

    yield nodebalancer_id, config_id, node_id, node_ip

    delete_target_id(target="nodebalancers", id=nodebalancer_id)
    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="module")
def simple_nodebalancer_with_config(linode_cloud_firewall):
    nodebalancer_id = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "create",
            "--region",
            "us-ord",
            "--client_conn_throttle",
            "20",
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
    config_id = exec_test_command(
        BASE_CMDS["nodebalancers"]
        + [
            "config-create",
            nodebalancer_id,
            "--port",
            "81",
            "--protocol",
            "http",
            "--algorithm",
            "leastconn",
            "--check_path",
            "/test",
            "--check_body",
            "it works",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    )

    yield nodebalancer_id, config_id

    delete_target_id(target="nodebalancers", id=nodebalancer_id)
