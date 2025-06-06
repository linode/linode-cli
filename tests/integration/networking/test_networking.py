import json
import re

import pytest
from _pytest.monkeypatch import MonkeyPatch

from tests.integration.helpers import delete_target_id, exec_test_command
from tests.integration.linodes.helpers_linodes import (
    create_linode,
    create_linode_and_wait,
)

BASE_CMD = ["linode-cli", "networking"]


@pytest.fixture(scope="package")
def test_linode_id(linode_cloud_firewall):
    linode_id = create_linode_and_wait(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="package")
def test_linode_id_shared_ipv4(linode_cloud_firewall):
    target_region = "us-mia"

    linode_ids = (
        create_linode(
            test_region=target_region, firewall_id=linode_cloud_firewall
        ),
        create_linode(
            test_region=target_region, firewall_id=linode_cloud_firewall
        ),
    )

    yield linode_ids

    for id in linode_ids:
        delete_target_id(target="linodes", id=id)


def has_shared_ip(linode_id: int, ip: str) -> bool:
    shared_ips = json.loads(
        exec_test_command(
            ["linode-cli", "linodes", "ips-list", "--json", linode_id]
        ).stdout.decode()
    )[0]["ipv4"]["shared"]
    for entry in shared_ips:
        if entry["address"] == ip:
            # Validate presence and type of interface_id
            assert "interface_id" in entry
            assert entry["interface_id"] is None or isinstance(
                entry["interface_id"], int
            )
            return True

    return False


def test_display_ips_for_available_linodes(test_linode_id):
    result = exec_test_command(
        BASE_CMD + ["ips-list", "--text", "--no-headers", "--delimiter", ","]
    ).stdout.decode()

    assert re.search(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", result)
    assert re.search(
        r"ipv4,True,[0-9]{1,3}\-[0-9]{1,3}\-[0-9]{1,3}\-[0-9]{1,3}\.ip.linodeusercontent.com,.*,[0-9][0-9][0-9][0-9][0-9][0-9][0-9]*",
        result,
    )
    assert re.search("ipv6,True,,.*,[0-9][0-9][0-9][0-9][0-9][0-9]*", result)
    assert re.search(
        r"(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))",
        result,
    )


@pytest.mark.smoke
def test_view_an_ip_address(test_linode_id):
    linode_id = test_linode_id
    linode_ipv4 = exec_test_command(
        [
            "linode-cli",
            "linodes",
            "view",
            linode_id,
            "--format",
            "ipv4",
            "--text",
            "--no-headers",
        ]
    ).stdout.rstrip()

    result = exec_test_command(
        BASE_CMD
        + [
            "ip-view",
            "--json",
            linode_ipv4,
        ]
    ).stdout.decode()

    data = json.loads(result)
    if isinstance(data, list):
        data = data[0]
    # Validate that the address is a proper IPv4 address
    assert re.match(r"^[0-9]{1,3}(\.[0-9]{1,3}){3}$", data["address"])

    # Validate that interface_id is present and either None or int
    assert (
        "interface_id" in data
    ), "`interface_id` field missing in IP view response"
    assert data["interface_id"] is None or isinstance(
        data["interface_id"], int
    ), f"`interface_id` is not None or int: {data['interface_id']}"


def test_allocate_additional_private_ipv4_address(test_linode_id):
    linode_id = test_linode_id

    result = exec_test_command(
        BASE_CMD
        + [
            "ip-add",
            "--type",
            "ipv4",
            "--linode_id",
            linode_id,
            "--delimiter",
            ",",
            "--public",
            "false",
            "--text",
            "--no-headers",
        ]
    ).stdout.decode()

    assert re.search(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", result)
    assert re.search(
        "ipv4,False,.*,[0-9][0-9][0-9][0-9][0-9][0-9][0-9]*", result
    )


def test_share_ipv4_address(
    test_linode_id_shared_ipv4, monkeypatch: MonkeyPatch
):
    target_linode, parent_linode = test_linode_id_shared_ipv4
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    # Allocate an IPv4 address on the parent Linode
    ip_address = json.loads(
        exec_test_command(
            BASE_CMD
            + [
                "ip-add",
                "--type",
                "ipv4",
                "--linode_id",
                parent_linode,
                "--json",
                "--public",
                "true",
            ]
        ).stdout.decode()
    )[0]["address"]

    # Share the IP address to the target Linode
    exec_test_command(
        BASE_CMD
        + [
            "ip-share",
            "--ips",
            ip_address,
            "--linode_id",
            target_linode,
            "--json",
        ]
    )

    assert has_shared_ip(target_linode, ip_address)

    # Remove the IP shares
    exec_test_command(
        BASE_CMD
        + [
            "ip-share",
            "--ips",
            "[]",
            "--linode_id",
            target_linode,
            "--json",
        ]
    )

    assert not has_shared_ip(target_linode, ip_address)
