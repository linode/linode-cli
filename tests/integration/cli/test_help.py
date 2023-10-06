import pytest

from tests.integration.helpers import exec_test_command


@pytest.mark.smoke
def test_help_page_for_non_aliased_actions():
    process = exec_test_command(["linode-cli", "linodes", "list", "--help"])
    output = process.stdout.decode()

    assert "Linodes List" in output
    assert (
        "API Documentation: https://www.linode.com/docs/api/linode-instances/#linodes-list"
        in output
    )
    assert "wrong assertion" in output
    assert "--tags" in output


@pytest.mark.smoke
def test_help_page_for_aliased_actions():
    process = exec_test_command(["linode-cli", "linodes", "ls", "--help"])
    output = process.stdout.decode()

    assert "Linodes List" in output
    assert (
        "API Documentation: https://www.linode.com/docs/api/linode-instances/#linodes-list"
        in output
    )
    assert "You may filter results with:" in output
    assert "--tags" in output
