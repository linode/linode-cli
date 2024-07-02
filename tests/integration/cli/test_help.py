import textwrap

import pytest

from tests.integration.helpers import (
    contains_at_least_one_of,
    exec_test_command,
)


@pytest.mark.smoke
def test_help_page_for_non_aliased_actions():
    process = exec_test_command(["linode-cli", "linodes", "list", "--help"])
    output = process.stdout.decode()
    wrapped_output = textwrap.fill(output, width=150).replace("\n", "")

    assert contains_at_least_one_of(
        wrapped_output, ["Linodes List", "List Linodes"]
    )

    assert contains_at_least_one_of(
        wrapped_output,
        [
            "API Documentation:  https://www.linode.com/docs/api/linode-instances/#linodes-list",
            "API Documentation:  https://www.linode.com/docs/api/linode-instances/#list-linodes",
        ],
    )

    assert "You may filter results with:" in wrapped_output
    assert "--tags" in wrapped_output


@pytest.mark.smoke
def test_help_page_for_aliased_actions():
    process = exec_test_command(["linode-cli", "linodes", "ls", "--help"])
    output = process.stdout.decode()
    wrapped_output = textwrap.fill(output, width=150).replace("\n", "")

    assert contains_at_least_one_of(
        wrapped_output, ["Linodes List", "List Linodes"]
    )

    assert contains_at_least_one_of(
        wrapped_output,
        [
            "API Documentation:  https://www.linode.com/docs/api/linode-instances/#linodes-list",
            "API Documentation:  https://www.linode.com/docs/api/linode-instances/#list-linodes",
        ],
    )

    assert "You may filter results with:" in wrapped_output
    assert "--tags" in wrapped_output
