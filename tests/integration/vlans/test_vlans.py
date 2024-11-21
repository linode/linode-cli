from tests.integration.helpers import assert_headers_in_lines, exec_test_command

BASE_CMD = ["linode-cli", "vlans"]


def test_list_vlans():
    types = (
        exec_test_command(
            BASE_CMD
            + [
                "ls",
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["region", "label", "linodes"]
    lines = types.splitlines()

    assert_headers_in_lines(headers, lines)


def test_list_vlans_help_menu():
    help_menu = (
        exec_test_command(
            BASE_CMD
            + [
                "ls",
                "--h",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert "linode-cli vlans ls" in help_menu
    assert (
        "https://techdocs.akamai.com/linode-api/reference/get-vlans"
        in help_menu
    )


def test_delete_vlans_help_menu():
    help_menu = (
        exec_test_command(
            BASE_CMD
            + [
                "delete",
                "--h",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert "linode-cli vlans delete [LABEL] [REGIONID]" in help_menu
    assert (
        "https://techdocs.akamai.com/linode-api/reference/delete-vlan"
        in help_menu
    )
