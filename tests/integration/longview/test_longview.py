import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
    get_random_text,
)


@pytest.mark.smoke
def test_create_longview_client():
    new_label = get_random_text(5) + "label"
    result = exec_test_command(
        BASE_CMDS["longview"]
        + [
            "create",
            "--label",
            new_label,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    )

    assert new_label in result


def test_longview_client_list():
    res = exec_test_command(
        BASE_CMDS["longview"] + ["list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["id", "label", "created"]
    assert_headers_in_lines(headers, lines)


def test_client_view():
    client_id = get_client_id()
    res = exec_test_command(
        BASE_CMDS["longview"] + ["view", client_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["id", "label", "created"]
    assert_headers_in_lines(headers, lines)


def test_update_longview_client_list():
    client_id = get_client_id()
    new_label = get_random_text(5) + "label"
    updated_label = exec_test_command(
        BASE_CMDS["longview"]
        + [
            "update",
            client_id,
            "--label",
            new_label,
            "--text",
            "--no-headers",
            "--format=label",
        ]
    )
    assert new_label == updated_label
    delete_target_id(target="longview", id=client_id)


def test_longview_plan_view():
    res = exec_test_command(
        BASE_CMDS["longview"] + ["plan-view", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["id", "label", "clients_included"]
    assert_headers_in_lines(headers, lines)


def test_longview_subscriptions_list():
    res = exec_test_command(
        BASE_CMDS["longview"]
        + ["subscriptions-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["id", "label", "clients_included"]
    assert_headers_in_lines(headers, lines)


def test_longview_subscriptions_list_view():
    subscriptions_id = get_subscriptions_id()
    res = exec_test_command(
        BASE_CMDS["longview"]
        + ["subscription-view", subscriptions_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["id", "label", "clients_included"]
    assert_headers_in_lines(headers, lines)


def get_client_id():
    client_id = exec_test_command(
        BASE_CMDS["longview"]
        + [
            "list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    first_id = client_id[0]

    return first_id


def get_subscriptions_id():
    subscriptions_id = exec_test_command(
        BASE_CMDS["longview"]
        + [
            "subscriptions-list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    first_id = subscriptions_id[0]

    return first_id
