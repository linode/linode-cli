from tests.integration.helpers import exec_test_command

BASE_CMD = ["linode-cli", "account"]


def test_account_transfer():
    res = (
        exec_test_command(BASE_CMD + ["transfer", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["billable", "quota", "used"]
    for header in headers:
        assert header in lines[0]


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
    for header in headers:
        assert header in lines[0]


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
    for header in headers:
        assert header in lines[0]
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
    for header in headers:
        assert header in lines[0]


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
    for header in headers:
        assert header in lines[0]
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
    for header in headers:
        assert header in lines[0]


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
    for header in headers:
        assert header in lines[0]


def test_account_logins_list():
    res = (
        exec_test_command(BASE_CMD + ["logins-list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    login_id = lines[1].split(",")[0]

    headers = ["ip", "username", "status"]
    for header in headers:
        assert header in lines[0]
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
    for header in headers:
        assert header in lines[0]


def test_account_setting_view():
    res = (
        exec_test_command(BASE_CMD + ["settings", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["longview_subscription", "network_helper"]
    for header in headers:
        assert header in lines[0]


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
    for header in headers:
        assert header in lines[0]
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
    for header in headers:
        assert header in lines[0]


def test_beta_list():
    res = (
        exec_test_command(
            ["linode-cli", "betas", "list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["label", "description"]
    for header in headers:
        assert header in lines[0]
