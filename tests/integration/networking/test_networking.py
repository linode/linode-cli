import ipaddress
import json
import re

import pytest
from _pytest.monkeypatch import MonkeyPatch

from tests.integration.helpers import (
    BASE_CMDS,
    DEFAULT_REGION,
    assert_headers_in_lines,
    exec_test_command,
)
from tests.integration.networking.fixtures import (  # noqa: F401
    get_linode_id,
    get_linode_ids_shared_ipv4,
)

RESERVED_IP_HEADERS = [
    "address",
    "type",
    "public",
    "rdns",
    "region",
    "linode_id",
    "interface_id",
    "reserved",
    "gateway",
    "prefix",
    "subnet_mask",
    "tags",
]


def has_shared_ip(linode_id: int, ip: str) -> bool:
    shared_ips = json.loads(
        exec_test_command(
            ["linode-cli", "linodes", "ips-list", "--json", linode_id]
        )
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


def verify_reserved_ip(result):
    assert isinstance(
        ipaddress.ip_address(result["address"]), ipaddress.IPv4Address
    )
    assert result["type"] == "ipv4"
    assert result["public"] == True
    assert result["region"] == DEFAULT_REGION
    assert not result["linode_id"]
    assert result["reserved"] == True


def test_display_ips_for_available_linodes(get_linode_id):
    result = exec_test_command(
        BASE_CMDS["networking"]
        + ["ips-list", "--text", "--no-headers", "--delimiter", ","]
    )

    assert re.search(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", result)
    assert re.search(
        r"ipv4,(False|True),\d{1,3}\-\d{1,3}\-\d{1,3}\-\d{1,3}\.ip\.linodeusercontent\.com,[a-zA-Z]{2}\-[a-zA-Z]{3}.*,\d*,\d*,(False|True)",
        result,
    )
    assert re.search("ipv6,True,,[a-zA-Z]{2}\-[a-zA-Z]{3}.*,\d*", result)
    assert re.search(
        r"(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))",
        result,
    )


@pytest.mark.smoke
def test_view_an_ip_address(get_linode_id):
    linode_id = get_linode_id
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
    )

    result = exec_test_command(
        BASE_CMDS["networking"]
        + [
            "ip-view",
            "--json",
            linode_ipv4,
        ]
    )

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


def test_allocate_additional_private_ipv4_address(get_linode_id):
    linode_id = get_linode_id

    result = exec_test_command(
        BASE_CMDS["networking"]
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
    )

    assert re.search(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", result)
    assert re.search(
        "ipv4,False,.*,[0-9][0-9][0-9][0-9][0-9][0-9][0-9]*", result
    )


@pytest.mark.smoke
@pytest.mark.parametrize(
    "create_reserved_ip, expected",
    [("test", ["test"]), (None, [])],
    indirect=["create_reserved_ip"],
)
def test_create_reserved_ip(create_reserved_ip, expected):
    res_ip_data = create_reserved_ip
    headers = list(res_ip_data.keys())

    assert_headers_in_lines(RESERVED_IP_HEADERS, [headers])
    verify_reserved_ip(res_ip_data)
    assert res_ip_data["tags"] == expected


@pytest.mark.parametrize("create_reserved_ip", ["test"], indirect=True)
def test_update_reserved_ip_tags(create_reserved_ip):
    res_ip_data = create_reserved_ip
    assert res_ip_data["tags"] == ["test"]

    result = json.loads(
        exec_test_command(
            BASE_CMDS["networking"]
            + [
                "reserved-ip-update",
                "--tags",
                "updated",
                "--tags",
                "updated2",
                res_ip_data["address"],
                "--json",
            ]
        )
    )[0]

    verify_reserved_ip(result)
    assert result["tags"] == ["updated", "updated2"]


def test_create_reserved_ip_assigned(create_reserved_ip, get_linode_id):
    res_ip_data = create_reserved_ip
    linode_id = get_linode_id

    exec_test_command(
        BASE_CMDS["networking"]
        + [
            "ip-assign",
            "--assignments.linode_id",
            linode_id,
            "--assignments.address",
            res_ip_data["address"],
            "--region",
            DEFAULT_REGION,
        ]
    )

    result = json.loads(
        exec_test_command(
            BASE_CMDS["linodes"]
            + [
                "ip-view",
                linode_id,
                res_ip_data["address"],
                "--json",
            ]
        )
    )[0]
    headers = list(result.keys())

    assert_headers_in_lines(RESERVED_IP_HEADERS[:-1], [headers])
    assert result["address"] == res_ip_data["address"]
    assert result["linode_id"] == int(linode_id)
    assert result["reserved"] == True
    assert "tags" not in headers
    assert "assigned_entity" in headers


def test_get_reserved_ip_types():
    headers_exp = [
        "id",
        "label",
        "price",
        "region_prices",
    ]
    result = json.loads(
        exec_test_command(
            BASE_CMDS["networking"]
            + [
                "reserved-ip-types-list",
                "--json",
            ]
        )
    )[0]
    headers = list(result.keys())
    prices = [result["price"]["hourly"], result["price"]["monthly"]]

    assert_headers_in_lines(headers_exp, [headers])
    assert result["id"] == "reserved-ipv4"
    assert result["label"] == "Reserved IPv4"
    assert any(price != 0 for price in prices)


def test_get_reserved_ip_view(create_reserved_ip):
    res_ip_data = create_reserved_ip
    result = json.loads(
        exec_test_command(
            BASE_CMDS["networking"]
            + [
                "reserved-ip-view",
                res_ip_data["address"],
                "--json",
            ]
        )
    )[0]
    headers = list(result.keys())

    assert_headers_in_lines(RESERVED_IP_HEADERS, [headers])
    verify_reserved_ip(result)


def test_get_reserved_ips_list(create_reserved_ip):
    result = exec_test_command(
        BASE_CMDS["networking"]
        + [
            "reserved-ips-list",
            "--text",
            "--no-headers",
            "--format",
            "reserved",
        ]
    ).splitlines()

    assert all(item == "True" for item in result)


def test_update_ephemeral_to_reserved(get_linode_id):
    linode_id = get_linode_id

    ephemeral_ip = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "view",
            linode_id,
            "--text",
            "--no-headers",
            "--format",
            "ipv4",
        ]
    ).split(" ")[0]

    exec_test_command(
        BASE_CMDS["networking"]
        + [
            "ip-update",
            ephemeral_ip,
            "--reserved",
            "true",
        ]
    )

    is_reserved = exec_test_command(
        BASE_CMDS["networking"]
        + [
            "reserved-ip-view",
            ephemeral_ip,
            "--text",
            "--no-headers",
            "--format",
            "reserved",
        ]
    )

    assert is_reserved == "True"


def test_allocate_reserved_ipv4_address(get_linode_id):
    linode_id = get_linode_id

    result = exec_test_command(
        BASE_CMDS["networking"]
        + [
            "ip-add",
            "--type",
            "ipv4",
            "--public",
            "true",
            "--linode_id",
            linode_id,
            "--reserved",
            "true",
            "--text",
            "--no-headers",
            "--format",
            "reserved",
        ]
    )

    assert result == "True"


def test_share_ipv4_address(
    get_linode_ids_shared_ipv4, monkeypatch: MonkeyPatch
):
    target_linode, parent_linode = get_linode_ids_shared_ipv4
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    # Allocate an IPv4 address on the parent Linode
    ip_address = json.loads(
        exec_test_command(
            BASE_CMDS["networking"]
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
        )
    )[0]["address"]

    # Share the IP address to the target Linode
    exec_test_command(
        BASE_CMDS["networking"]
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
        BASE_CMDS["networking"]
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
