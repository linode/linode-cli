import pytest
import re

from tests.integration.linodes.helpers_linodes import (
    DEFAULT_TEST_IMAGE,
    exec_failing_test_command,
    exec_test_command,
    os,
    remove_all,
)

BASE_CMD = ["linode-cli", "nodebalancers"]
nodebalancer_created = "[0-9]+,balancer[0-9]+,us-east,[0-9]+-[0-9]+-[0-9]+-[0-9]+.ip.linodeusercontent.com,0"


@pytest.fixture(scope="session", autouse=True)
def setup_test_node_balancers():
    # create a default nodebalancer
    exec_test_command(
        BASE_CMD
        + [
            "create",
            "--region",
            "us-east",
            "--text",
            "--delimiter",
            ",",
            "--format",
            "id,label,region,hostname,client_conn_throttle",
        ]
    ).stdout.decode()
    # create one standard config
    nodebalancer_id = get_nodebalancer_id()
    exec_test_command(
        BASE_CMD
        + [
            "config-create",
            nodebalancer_id,
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ]
    ).stdout.decode()

    # create a default node
    node_ip = (
        os.popen(
            "linode-cli linodes create --root_pass aComplex@Password --booted true --region us-east --type g6-standard-2 --private_ip true --image "
            + DEFAULT_TEST_IMAGE
            + ' --text --no-headers --format "ip_address" | egrep -o "192.168.[0-9]{1,3}.[0-9]{1,3}"'
        )
        .read()
        .rstrip()
    )
    node_label = "defaultnode1"
    config_id = get_config_id(nodebalancer_id=nodebalancer_id)

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
        ]
    ).stdout.decode()

    yield "setup"
    try:
        remove_all(target="nodebalancers")
        remove_all(target="linodes")
    except:
        "Failed to remove all linodes/nodebalancers in teardown.."


# get helpers
def get_nodebalancer_id():
    nb_id = (
        exec_test_command(
            BASE_CMD + ["list", "--format", "id", "--text", "--no-headers"]
        )
        .stdout.decode()
        .split()
    )
    return nb_id[0]


def get_config_id(nodebalancer_id: str):
    conf_id = (
        exec_test_command(
            BASE_CMD
            + [
                "configs-list",
                nodebalancer_id,
                "--format",
                "id",
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .split()
    )
    return conf_id[0]


def get_node_id(nodebalancer_id: str, config_id: str):
    node_id = (
        exec_test_command(
            BASE_CMD
            + [
                "nodes-list",
                nodebalancer_id,
                config_id,
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .split()
    )
    return node_id[0]


def get_node_ip(nodebalancer_id: str, config_id: str, node_id: str):
    node_ip = (
        exec_test_command(
            BASE_CMD
            + [
                "node-view",
                nodebalancer_id,
                config_id,
                node_id,
                "--format",
                "address",
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .split()
    )
    return node_ip[0]


def test_fail_to_create_nodebalancer_without_region():
    result = exec_failing_test_command(
        BASE_CMD + ["create", "--text", "--no-headers"]
    ).stderr.decode()
    assert "Request failed: 400" in result
    assert "region	region is required" in result


def test_create_nodebalancer_with_default_conf():
    result = exec_test_command(
        BASE_CMD
        + [
            "create",
            "--region",
            "us-east",
            "--text",
            "--delimiter",
            ",",
            "--format",
            "id,label,region,hostname,client_conn_throttle",
        ]
    ).stdout.decode()
    assert re.search(nodebalancer_created, result)


def test_list_nodebalancers_and_status():
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


def test_display_public_ipv4_for_nodebalancer():
    nodebalancer_id = get_nodebalancer_id()

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
    assert re.search("^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", result)


def test_fail_to_view_nodebalancer_with_invalid_id():
    result = exec_failing_test_command(
        BASE_CMD + ["view", "535", "--text", "--no-headers"]
    ).stderr.decode()

    assert "Request failed: 404" in result


def test_create_standard_configuration_profile():
    nodebalancer_id = get_nodebalancer_id()

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


def test_view_configuration_profile():
    nodebalancer_id = get_nodebalancer_id()
    config_id = get_config_id(nodebalancer_id=nodebalancer_id)

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


def test_add_node_to_conf_profile():
    node_ip = (
        os.popen(
            "linode-cli linodes create --root_pass aComplex@Password --booted true --region us-east --type g6-standard-2 --private_ip true --image "
            + DEFAULT_TEST_IMAGE
            + ' --text --no-headers --format "ip_address" | egrep -o "192.168.[0-9]{1,3}.[0-9]{1,3}"'
        )
        .read()
        .rstrip()
    )
    node_label = "testnode1"
    nodebalancer_id = get_nodebalancer_id()
    config_id = get_config_id(nodebalancer_id=nodebalancer_id)

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


def test_update_node_label():
    nodebalancer_id = get_nodebalancer_id()
    config_id = get_config_id(nodebalancer_id=nodebalancer_id)
    node_id = get_node_id(nodebalancer_id=nodebalancer_id, config_id=config_id)
    node_ip = get_node_ip(
        nodebalancer_id=nodebalancer_id, config_id=config_id, node_id=node_id
    )
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
        "[0-9]+," + new_label + "," + node_ip + ",Unknown,100,accept", result
    )


def test_update_node_port():
    nodebalancer_id = get_nodebalancer_id()
    config_id = get_config_id(nodebalancer_id=nodebalancer_id)
    node_id = get_node_id(nodebalancer_id=nodebalancer_id, config_id=config_id)
    node_ip = get_node_ip(
        nodebalancer_id=nodebalancer_id, config_id=config_id, node_id=node_id
    )

    updated_port = ":23"

    new_address = node_ip.replace(":80", updated_port)

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

    assert ("[0-9]+,.," + new_address + ",Unknown,100,accept", result)


def test_fail_to_update_node_to_public_ipv4_address():
    nodebalancer_id = get_nodebalancer_id()
    config_id = get_config_id(nodebalancer_id=nodebalancer_id)
    node_id = get_node_id(nodebalancer_id=nodebalancer_id, config_id=config_id)

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
        ]
    ).stderr.decode()

    assert "Request failed: 400" in result
    assert "Must begin with 192.168" in result


# @pytest.mark.dependency(test_update_node_port())
def test_remove_node_from_configuration_profile():
    nodebalancer_id = get_nodebalancer_id()
    config_id = get_config_id(nodebalancer_id=nodebalancer_id)
    node_id = get_node_id(nodebalancer_id=nodebalancer_id, config_id=config_id)

    exec_test_command(
        BASE_CMD + ["node-delete", nodebalancer_id, config_id, node_id]
    )


# Test below this needs to be ran last and in order
@pytest.fixture(scope="session")
def test_update_the_port_of_a_configuration_profile():
    nodebalancer_id = get_nodebalancer_id()
    config_id = get_config_id(nodebalancer_id=nodebalancer_id)

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


@pytest.fixture(scope="session")
def test_add_additional_configuration_profile():
    nodebalancer_id = get_nodebalancer_id()

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
        "[0-9]+,81,http,roundrobin,none,True,recommended,,", result
    )


@pytest.mark.usefixtures(
    "test_add_additional_configuration_profile",
    "test_update_the_port_of_a_configuration_profile",
)
def test_list_multiple_configuration_profile():
    nodebalancer_id = get_nodebalancer_id()

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
        "[0-9]+,81,http,roundrobin,none,True,recommended,,", result
    )
    assert re.search(
        "[0-9]+,10700,tcp,roundrobin,none,True,recommended,,", result
    )
