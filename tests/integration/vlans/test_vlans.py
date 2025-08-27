from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_test_command,
)


def test_list_vlans():
    types = exec_test_command(
        BASE_CMDS["vlans"]
        + [
            "ls",
            "--text",
        ]
    )

    headers = ["region", "label", "linodes"]
    lines = types.splitlines()

    assert_headers_in_lines(headers, lines)


def test_list_vlans_help_menu():
    help_menu = exec_test_command(
        BASE_CMDS["vlans"]
        + [
            "ls",
            "--h",
        ]
    )

    assert "linode-cli vlans ls" in help_menu
    assert (
        "https://techdocs.akamai.com/linode-api/reference/get-vlans"
        in help_menu
    )


def test_delete_vlans_help_menu():
    help_menu = exec_test_command(
        BASE_CMDS["vlans"]
        + [
            "delete",
            "--h",
        ]
    )

    assert "linode-cli vlans delete [LABEL] [REGIONID]" in help_menu
    assert (
        "https://techdocs.akamai.com/linode-api/reference/delete-vlan"
        in help_menu
    )
