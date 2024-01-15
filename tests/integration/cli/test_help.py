import pytest
import textwrap
from tests.integration.helpers import exec_test_command


@pytest.mark.smoke
def test_help_page_for_non_aliased_actions():
    process = exec_test_command(["linode-cli", "linodes", "list", "--help"])
    output = process.stdout.decode()
    wrapped_output = textwrap.fill(output, width=150).replace("\n", "")

    assert "Linodes List" in wrapped_output
    assert (
        "API Documentation:  https://www.linode.com/docs/api/linode-instances/#linodes-list"
        in wrapped_output
    )
    assert "You may filter results with:" in wrapped_output
    assert "--tags" in wrapped_output


@pytest.mark.smoke
def test_help_page_for_aliased_actions():
    process = exec_test_command(["linode-cli", "linodes", "ls", "--help"])
    output = process.stdout.decode()
    wrapped_output = textwrap.fill(output, width=150).replace("\n", "")

    assert "Linodes List" in wrapped_output
    assert (
        "API Documentation:  https://www.linode.com/docs/api/linode-instances/#linodes-list"
        in wrapped_output
    )
    assert "You may filter results with:" in wrapped_output
    assert "--tags" in wrapped_output
