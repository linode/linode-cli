import ipaddress
import json
import re

import pytest
from _pytest.monkeypatch import MonkeyPatch

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_test_command,
)
from tests.integration.linodes.helpers import DEFAULT_REGION
from tests.integration.networking.fixtures import (  # noqa: F401
    create_reserved_ip,
    get_command_heads_and_vals,
    test_linode_id,
    test_linode_id_shared_ipv4,
)

RESERVED_IP_HEADERS = [
    "address",
    "type",
    "public",
    "rdns",
    "linode_id",
    "reserved",
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


def verify_reserved_ip(reserved_ip):
    assert isinstance(
        ipaddress.ip_address(reserved_ip[0]), ipaddress.IPv4Address
    )
    assert reserved_ip[1] == "ipv4"
    assert reserved_ip[2] == "True"
    assert reserved_ip[4] == DEFAULT_REGION
    assert not reserved_ip[5]
    assert reserved_ip[7] == "True"
    # TODO: To be clarified if it should be returned in CLI
    # assert reserved_ip["assigned_entity"] is None


def test_display_ips_for_available_linodes(test_linode_id):
    result = exec_test_command(
        BASE_CMDS["networking"]
        + ["ips-list", "--text", "--no-headers", "--delimiter", ","]
    )

    assert re.search(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", result)
    assert re.search(
        r"ipv4,True,(False|True),[0-9]{1,3}\-[0-9]{1,3}\-[0-9]{1,3}\-[0-9]{1,3}\.ip\.linodeusercontent\.com,[0-9]*",
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


def test_allocate_additional_private_ipv4_address(test_linode_id):
    linode_id = test_linode_id

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
@pytest.mark.parametrize("create_reserved_ip", ["test", None], indirect=True)
def test_create_reserved_ip(create_reserved_ip):
    headers, reserved_ip = create_reserved_ip
    assert_headers_in_lines(RESERVED_IP_HEADERS, [headers])
    verify_reserved_ip(reserved_ip)

    tags = reserved_ip[-1]
    assert tags == "test" if tags else tags == ""


@pytest.mark.parametrize("create_reserved_ip", ["test"], indirect=True)
def test_update_reserved_ip_tags(create_reserved_ip):
    _, reserved_ip = create_reserved_ip
    assert reserved_ip[-1] == "test"

    result = exec_test_command(
        BASE_CMDS["networking"]
        + [
            "reserved-ip-update",
            "--tags",
            "updated",
            "--tags",
            "updated2",
            reserved_ip[0],
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).split(",")
    verify_reserved_ip(result)
    assert result[-1] == "updated updated2"


def test_create_reserved_ip_assigned(create_reserved_ip, test_linode_id):
    _, reserved_ip = create_reserved_ip
    linode_id = test_linode_id

    exec_test_command(
        BASE_CMDS["networking"]
        + [
            "ip-assign",
            "--assignments.linode_id",
            linode_id,
            "--assignments.address",
            reserved_ip[0],
            "--region",
            DEFAULT_REGION,
        ]
    )

    command = BASE_CMDS["linodes"] + [
        "ip-view",
        linode_id,
        reserved_ip[0],
        "--text",
        "--delimiter",
        ",",
    ]
    headers, values = get_command_heads_and_vals(command)

    assert_headers_in_lines(RESERVED_IP_HEADERS[:-1], [headers])
    # TODO: To be clarified if tags should be returned in CLI (currently it is)
    # assert "tags" not in headers
    assert values[0] == reserved_ip[0]
    assert str(values[5]) == linode_id
    assert values[7] == "True"


def test_get_reserved_ip_types():
    headers_exp = ["id", "label", "price.hourly", "price.monthly"]
    command = BASE_CMDS["networking"] + [
        "reserved-ip-types-list",
        "--text",
        "--delimiter",
        ",",
    ]
    headers, values = get_command_heads_and_vals(command)

    assert_headers_in_lines(headers_exp, [headers])
    assert values[0] == "reserved-ipv4"
    assert values[1] == "Reserved IPv4"
    assert any(price != 0 for price in values[2:4])


def test_get_reserved_ip_view(create_reserved_ip):
    _, reserved_ip = create_reserved_ip
    command = BASE_CMDS["networking"] + [
        "reserved-ip-view",
        reserved_ip[0],
        "--text",
        "--delimiter",
        ",",
    ]
    headers, values = get_command_heads_and_vals(command)

    assert_headers_in_lines(RESERVED_IP_HEADERS, [headers])
    verify_reserved_ip(values)


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


def test_update_ephemeral_to_reserved(test_linode_id):
    linode_id = test_linode_id

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


def test_share_ipv4_address(
    test_linode_id_shared_ipv4, monkeypatch: MonkeyPatch
):
    target_linode, parent_linode = test_linode_id_shared_ipv4
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
