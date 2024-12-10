import pytest

from tests.integration.helpers import assert_headers_in_lines, exec_test_command

BASE_CMD = ["linode-cli", "profile"]


def test_profile_view():
    res = (
        exec_test_command(BASE_CMD + ["view", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["username", "email", "restricted"]
    assert_headers_in_lines(headers, lines)


def test_profile_apps_list():
    res = (
        exec_test_command(BASE_CMD + ["apps-list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["label", "scopes", "website"]
    assert_headers_in_lines(headers, lines)


def test_profile_devices_list():
    res = (
        exec_test_command(
            BASE_CMD + ["devices-list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["created", "expiry", "user_agent"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def login_ids():
    login_id = (
        exec_test_command(
            BASE_CMD
            + [
                "logins-list",
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )
    first_login_id = login_id[0]
    yield first_login_id


def test_profile_login_list():
    res = (
        exec_test_command(BASE_CMD + ["logins-list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["datetime", "username", "status"]
    assert_headers_in_lines(headers, lines)


def test_profile_login_view(login_ids):
    login_id = login_ids
    res = (
        exec_test_command(
            BASE_CMD + ["login-view", login_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["datetime", "username", "status"]
    assert_headers_in_lines(headers, lines)


def test_security_questions_list():
    res = (
        exec_test_command(
            [
                "linode-cli",
                "security-questions",
                "list",
                "--text",
                "--delimiter=,",
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["security_questions.id", "security_questions.question"]
    assert_headers_in_lines(headers, lines)


def test_profile_token_list():
    res = (
        exec_test_command(BASE_CMD + ["tokens-list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["label", "scopes", "token"]
    assert_headers_in_lines(headers, lines)


def test_sshkeys_list():
    res = (
        exec_test_command(
            [
                "linode-cli",
                "sshkeys",
                "list",
                "--text",
                "--delimiter=,",
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["label", "ssh_key"]
    assert_headers_in_lines(headers, lines)
