import json

import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_test_command,
)


def test_account_transfer():
    res = exec_test_command(
        BASE_CMDS["account"] + ["transfer", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["billable", "quota", "used"]
    assert_headers_in_lines(headers, lines)


def test_available_service():
    res = exec_test_command(
        BASE_CMDS["account"] + ["get-availability", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["region", "unavailable"]
    assert_headers_in_lines(headers, lines)


def test_region_availability():
    res = exec_test_command(
        BASE_CMDS["account"]
        + ["get-account-availability", "us-east", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["region", "unavailable"]
    assert_headers_in_lines(headers, lines)


def test_event_list():
    res = exec_test_command(
        ["linode-cli", "events", "list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["entity.label", "username"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def get_event_id():
    event_id = exec_test_command(
        [
            "linode-cli",
            "events",
            "list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    first_id = event_id[0].split(",")[0]
    yield first_id


def test_event_view(get_event_id):
    event_id = get_event_id
    res = exec_test_command(
        [
            "linode-cli",
            "events",
            "view",
            event_id,
            "--text",
            "--delimiter=,",
        ]
    )
    lines = res.splitlines()

    headers = ["id", "action"]
    assert_headers_in_lines(headers, lines)


def test_event_read(get_event_id):
    event_id = get_event_id
    process = exec_test_command(
        [
            "linode-cli",
            "events",
            "mark-read",
            event_id,
            "--text",
            "--delimiter=,",
        ]
    )


def test_event_seen(get_event_id):
    event_id = get_event_id
    process = exec_test_command(
        [
            "linode-cli",
            "events",
            "mark-seen",
            event_id,
            "--text",
            "--delimiter=,",
        ]
    )


def test_account_invoice_list():
    res = exec_test_command(
        BASE_CMDS["account"] + ["invoices-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["billing_source", "tax", "subtotal"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def get_invoice_id():
    invoice_id = exec_test_command(
        BASE_CMDS["account"]
        + [
            "invoices-list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    first_id = invoice_id[0]
    yield first_id


def test_account_invoice_view(get_invoice_id):
    invoice_id = get_invoice_id
    res = exec_test_command(
        BASE_CMDS["account"]
        + ["invoice-view", invoice_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["billing_source", "tax", "subtotal"]
    assert_headers_in_lines(headers, lines)


def test_account_invoice_items(get_invoice_id):
    invoice_id = get_invoice_id
    res = exec_test_command(
        BASE_CMDS["account"]
        + ["invoice-items", invoice_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["label", "from", "to"]
    assert_headers_in_lines(headers, lines)


def test_account_logins_list():
    res = exec_test_command(
        BASE_CMDS["account"] + ["logins-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["ip", "username", "status"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def get_login_id():
    login_id = exec_test_command(
        BASE_CMDS["account"]
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
    first_id = login_id[0]
    yield first_id


def test_account_login_view(get_login_id):
    login_id = get_login_id
    res = exec_test_command(
        BASE_CMDS["account"]
        + ["login-view", login_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["ip", "username", "status"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def test_account_setting_view():
    expected_headers = [
        "longview_subscription",
        "network_helper",
        "interfaces_for_new_linodes",
    ]

    settings_text = (
        exec_test_command(BASE_CMDS + ["settings", "--text", "--delimiter=,"])
        .stdout.decode()
        .strip()
    )
    lines = settings_text.splitlines()
    headers = lines[0].split(",")

    for expected in expected_headers:
        assert (
            expected in headers
        ), f"Expected header '{expected}' not found in CLI output"

    # Fetch current interfaces setting
    settings_json = exec_test_command(
        BASE_CMDS + ["settings", "--json"]
    ).stdout.decode()
    original_value = json.loads(settings_json)[0]["interfaces_for_new_linodes"]

    yield original_value

    # Restore original setting after test
    exec_test_command(
        BASE_CMDS
        + [
            "settings-update",
            "--interfaces_for_new_linodes",
            original_value,
        ]
    )


def test_update_interfaces_setting(test_account_setting_view):
    original_value = test_account_setting_view

    # Define valid values different from the original
    valid_options = [
        "legacy_config_only",
        "legacy_config_default_but_linode_allowed",
        "linode_default_but_legacy_config_allowed",
        "linode_only",
    ]

    # Select a different value for testing
    new_value = next(val for val in valid_options if val != original_value)

    # Update the setting
    exec_test_command(
        BASE_CMDS
        + [
            "settings-update",
            "--interfaces_for_new_linodes",
            new_value,
        ]
    )

    # Verify the setting was updated
    updated_json = exec_test_command(
        BASE_CMDS + ["settings", "--json"]
    ).stdout.decode()
    updated_value = json.loads(updated_json)[0]["interfaces_for_new_linodes"]

    assert (
        updated_value == new_value
    ), f"Expected {new_value}, got {updated_value}"


def test_user_list():
    res = exec_test_command(
        ["linode-cli", "users", "list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["email", "username"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def username():
    user_id = exec_test_command(
        [
            "linode-cli",
            "users",
            "list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "username",
        ]
    ).splitlines()
    first_id = user_id[0].split(",")[0]
    yield first_id


def test_user_view(username: str):
    res = exec_test_command(
        ["linode-cli", "users", "view", username, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["email", "username"]
    assert_headers_in_lines(headers, lines)


def test_payment_method_list():
    res = exec_test_command(
        ["linode-cli", "payment-methods", "list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["type", "is_default"]
    assert_headers_in_lines(headers, lines)


def test_payment_list():
    res = exec_test_command(
        BASE_CMDS["account"] + ["payments-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["date", "usd"]
    assert_headers_in_lines(headers, lines)


def test_service_transfers():
    res = exec_test_command(
        [
            "linode-cli",
            "service-transfers",
            "list",
            "--text",
            "--delimiter=,",
        ]
    )
    lines = res.splitlines()

    headers = ["token", "expiry", "is_sender"]
    assert_headers_in_lines(headers, lines)


def test_maintenance_list():
    res = exec_test_command(
        BASE_CMDS["account"] + ["maintenance-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["entity.type", "entity.label"]
    assert_headers_in_lines(headers, lines)


def test_notifications_list():
    res = exec_test_command(
        BASE_CMDS["account"] + ["notifications-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["label", "severity"]
    assert_headers_in_lines(headers, lines)


def test_clients_list():
    res = exec_test_command(
        BASE_CMDS["account"] + ["clients-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["label", "status"]
    assert_headers_in_lines(headers, lines)
