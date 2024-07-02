import textwrap

import pytest

from tests.integration.helpers import exec_test_command


@pytest.mark.smoke
def test_help_page_for_non_aliased_actions():
    process = exec_test_command(["linode-cli", "linodes", "list", "--help"])
    output = process.stdout.decode()
    wrapped_output = textwrap.fill(output, width=150).replace("\n", "")

    assert any(v in wrapped_output for v in ("Linodes List", "List Linodes"))

    assert any(
        f"API Documentation:  https://www.linode.com/docs/api/linode-instances/#{v}"
        in wrapped_output
        for v in ("linodes-list", "list-linodes")
    )

    assert "You may filter results with:" in wrapped_output
    assert "--tags" in wrapped_output


@pytest.mark.smoke
def test_help_page_for_aliased_actions():
    process = exec_test_command(["linode-cli", "linodes", "ls", "--help"])
    output = process.stdout.decode()
    wrapped_output = textwrap.fill(output, width=150).replace("\n", "")

    assert any(v in wrapped_output for v in ("Linodes List", "List Linodes"))

    assert any(
        f"API Documentation:  https://www.linode.com/docs/api/linode-instances/#{v}"
        in wrapped_output
        for v in ("linodes-list", "list-linodes")
    )

    assert "You may filter results with:" in wrapped_output
    assert "--tags" in wrapped_output
