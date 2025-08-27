import textwrap

import pytest

from tests.integration.helpers import (
    contains_at_least_one_of,
    exec_failing_test_command,
    exec_test_command,
)


@pytest.mark.smoke
def test_help_page_for_non_aliased_actions():
    output = exec_test_command(["linode-cli", "linodes", "list", "--help"])
    wrapped_output = textwrap.fill(output, width=180).replace("\n", "")

    assert contains_at_least_one_of(
        wrapped_output, ["Linodes List", "List Linodes"]
    )

    assert contains_at_least_one_of(
        wrapped_output,
        [
            "API Documentation:",
            "https://techdocs.akamai.com/linode-api/reference/",
        ],
    )

    assert "You may filter results with:" in wrapped_output
    assert "--tags" in wrapped_output


@pytest.mark.smoke
def test_help_page_for_aliased_actions():
    output = exec_test_command(["linode-cli", "linodes", "ls", "--help"])
    wrapped_output = textwrap.fill(output, width=180).replace("\n", "")

    assert contains_at_least_one_of(
        wrapped_output, ["Linodes List", "List Linodes"]
    )

    assert contains_at_least_one_of(
        wrapped_output,
        [
            "API Documentation:",
            "https://techdocs.akamai.com/linode-api/reference/",
        ],
    )

    assert "You may filter results with:" in wrapped_output
    assert "--tags" in wrapped_output


def test_debug_output_contains_request_url(monkeypatch: pytest.MonkeyPatch):
    env_vars = {
        "LINODE_CLI_API_HOST": "api.linode.com",
        "LINODE_CLI_API_VERSION": "v4",
        "LINODE_CLI_API_SCHEME": "https",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    output = exec_failing_test_command(
        [
            "linode-cli",
            "linodes",
            "update",
            "--label",
            "foobar",
            "12345",
            "--debug",
        ]
    )
    wrapped_output = textwrap.fill(output, width=180).replace("\n", "")

    assert (
        "PUT https://api.linode.com/v4/linode/instances/12345" in wrapped_output
    )
