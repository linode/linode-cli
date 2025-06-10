import pytest

from tests.integration.beta.helpers import get_beta_id
from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_test_command,
)


def test_beta_list():
    res = exec_test_command(
        BASE_CMDS["betas"] + ["list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    if len(lines) < 2 or len(lines[1].split(",")) == 0:
        pytest.skip("No beta program available to test")
    else:
        headers = ["label", "description"]
        assert_headers_in_lines(headers, lines)


def test_beta_view():
    beta_id = get_beta_id()
    if beta_id is None:
        pytest.skip("No beta program available to test")
    else:
        res = exec_test_command(
            BASE_CMDS["betas"] + ["view", beta_id, "--text", "--delimiter=,"]
        )
        lines = res.splitlines()
        headers = ["label", "description"]
        assert_headers_in_lines(headers, lines)


def test_beta_enrolled():
    res = exec_test_command(
        BASE_CMDS["betas"] + ["enrolled", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["label", "enrolled"]
    assert_headers_in_lines(headers, lines)
