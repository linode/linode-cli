from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_test_command,
)


def test_profile_view():
    res = exec_test_command(
        BASE_CMDS["profile"] + ["view", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["username", "email", "restricted"]
    assert_headers_in_lines(headers, lines)


def test_profile_apps_list():
    res = exec_test_command(
        BASE_CMDS["profile"] + ["apps-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["label", "scopes", "website"]
    assert_headers_in_lines(headers, lines)


def test_profile_devices_list():
    res = exec_test_command(
        BASE_CMDS["profile"] + ["devices-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["created", "expiry", "user_agent"]
    assert_headers_in_lines(headers, lines)


def get_login_id():
    login_id = exec_test_command(
        BASE_CMDS["profile"]
        + [
            "logins-list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    first_login_id = login_id[0]
    return first_login_id


def test_profile_login_list():
    res = exec_test_command(
        BASE_CMDS["profile"] + ["logins-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["datetime", "username", "status"]
    assert_headers_in_lines(headers, lines)


def test_profile_login_view():
    login_id = get_login_id()
    res = exec_test_command(
        BASE_CMDS["profile"]
        + ["login-view", login_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["datetime", "username", "status"]
    assert_headers_in_lines(headers, lines)


def test_security_questions_list():
    res = exec_test_command(
        [
            "linode-cli",
            "security-questions",
            "list",
            "--text",
            "--delimiter=,",
        ]
    )
    lines = res.splitlines()
    headers = ["security_questions.id", "security_questions.question"]
    assert_headers_in_lines(headers, lines)


def test_profile_token_list():
    res = exec_test_command(
        BASE_CMDS["profile"] + ["tokens-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["label", "scopes", "token"]
    assert_headers_in_lines(headers, lines)


def test_sshkeys_list():
    res = exec_test_command(
        [
            "linode-cli",
            "sshkeys",
            "list",
            "--text",
            "--delimiter=,",
        ]
    )
    lines = res.splitlines()
    headers = ["label", "ssh_key"]
    assert_headers_in_lines(headers, lines)
