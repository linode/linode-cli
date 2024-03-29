import pytest

from tests.integration.helpers import assert_headers_in_lines, exec_test_command

BASE_CMD = ["linode-cli", "betas"]


def test_beta_list():
    res = (
        exec_test_command(BASE_CMD + ["list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    if len(lines) < 2 or len(lines[1].split(",")) == 0:
        pytest.skip("No beta program available to test")
    else:
        beta_id = lines[1].split(",")[0]
        headers = ["label", "description"]
        assert_headers_in_lines(headers, lines)
        return beta_id


def test_beta_view():
    beta_id = test_beta_list()
    if beta_id is None:
        pytest.skip("No beta program available to test")
    else:
        res = (
            exec_test_command(
                BASE_CMD + ["view", beta_id, "--text", "--delimiter=,"]
            )
            .stdout.decode()
            .rstrip()
        )
        lines = res.splitlines()
        headers = ["label", "description"]
        assert_headers_in_lines(headers, lines)


def test_beta_enrolled():
    res = (
        exec_test_command(BASE_CMD + ["enrolled", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["label", "enrolled"]
    assert_headers_in_lines(headers, lines)
