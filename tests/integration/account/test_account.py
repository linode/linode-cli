from tests.integration.helpers import assert_headers_in_lines, exec_test_command

BASE_CMD = ["linode-cli", "account"]


def test_account_transfer():
    res = (
        exec_test_command(BASE_CMD + ["transfer", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["billable", "quota", "used"]
    assert_headers_in_lines(headers, lines)


def test_region_availability():
    res = (
        exec_test_command(
            BASE_CMD
            + ["get-account-availability", "us-east", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["region", "unavailable"]
    assert_headers_in_lines(headers, lines)


def test_event_list():
    res = (
        exec_test_command(
            ["linode-cli", "events", "list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    event_id = lines[1].split(",")[0]

    headers = ["entity.label", "username"]
    assert_headers_in_lines(headers, lines)
    return event_id


def test_event_view():
    event_id = test_event_list()
    res = (
        exec_test_command(
            [
                "linode-cli",
                "events",
                "view",
                event_id,
                "--text",
                "--delimiter=,",
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["id", "action"]
    assert_headers_in_lines(headers, lines)


def test_account_invoice_list():
    res = (
        exec_test_command(
            BASE_CMD + ["invoices-list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    invoice_id = lines[1].split(",")[0]

    headers = ["billing_source", "tax", "subtotal"]
    assert_headers_in_lines(headers, lines)
    return invoice_id


def test_account_invoice_view():
    invoice_id = test_account_invoice_list()
    res = (
        exec_test_command(
            BASE_CMD + ["invoice-view", invoice_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["billing_source", "tax", "subtotal"]
    assert_headers_in_lines(headers, lines)


def test_account_invoice_items():
    invoice_id = test_account_invoice_list()
    res = (
        exec_test_command(
            BASE_CMD + ["invoice-items", invoice_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["label", "from", "to"]
    assert_headers_in_lines(headers, lines)


def test_account_logins_list():
    res = (
        exec_test_command(BASE_CMD + ["logins-list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    login_id = lines[1].split(",")[0]

    headers = ["ip", "username", "status"]
    assert_headers_in_lines(headers, lines)
    return login_id


def test_account_login_view():
    login_id = test_account_logins_list()
    res = (
        exec_test_command(
            BASE_CMD + ["login-view", login_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["ip", "username", "status"]
    assert_headers_in_lines(headers, lines)


def test_account_setting_view():
    res = (
        exec_test_command(BASE_CMD + ["settings", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["longview_subscription", "network_helper"]
    assert_headers_in_lines(headers, lines)


def test_user_list():
    res = (
        exec_test_command(
            ["linode-cli", "users", "list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    user_id = lines[1].split(",")[0]

    headers = ["email", "username"]
    assert_headers_in_lines(headers, lines)
    return user_id


def test_user_view():
    user_id = test_user_list()
    res = (
        exec_test_command(
            ["linode-cli", "users", "view", user_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["email", "username"]
    assert_headers_in_lines(headers, lines)


def test_payment_method_list():
    res = (
        exec_test_command(
            ["linode-cli", "payment-methods", "list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["type", "is_default"]
    assert_headers_in_lines(headers, lines)


def test_payment_list():
    res = (
        exec_test_command(
            BASE_CMD + ["payments-list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["date", "usd"]
    assert_headers_in_lines(headers, lines)


def test_service_transfers():
    res = (
        exec_test_command(
            [
                "linode-cli",
                "service-transfers",
                "list",
                "--text",
                "--delimiter=,",
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["token", "expiry", "is_sender"]
    assert_headers_in_lines(headers, lines)
