import time

from tests.integration.helpers import (
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "longview"]


def test_create_longview_client():
    new_label = str(time.time_ns()) + "label"
    exec_test_command(
        BASE_CMD
        + [
            "create",
            "--label",
            new_label,
            "--text",
            "--no-headers",
        ]
    )


def test_longview_client_list():
    res = (
        exec_test_command(BASE_CMD + ["list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    client_id = lines[1].split(",")[0]

    headers = ["id", "label", "created"]
    assert_headers_in_lines(headers, lines)
    return client_id


def test_client_view():
    client_id = test_longview_client_list()
    res = (
        exec_test_command(
            BASE_CMD + ["view", client_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["id", "label", "created"]
    assert_headers_in_lines(headers, lines)


def test_update_longview_client_list():
    client_id = test_longview_client_list()
    new_label = str(time.time_ns()) + "label"
    updated_label = (
        exec_test_command(
            BASE_CMD
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
        .stdout.decode()
        .rstrip()
    )
    assert new_label == updated_label
    delete_target_id(target="longview", id=client_id)


def test_longview_plan_view():
    res = (
        exec_test_command(BASE_CMD + ["plan-view", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["id", "label", "clients_included"]
    assert_headers_in_lines(headers, lines)


def test_longview_subscriptions_list():
    res = (
        exec_test_command(
            BASE_CMD + ["subscriptions-list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    subscriptions_id = lines[1].split(",")[0]

    headers = ["id", "label", "clients_included"]
    assert_headers_in_lines(headers, lines)
    return subscriptions_id


def test_longview_subscriptions_list_view():
    subscriptions_id = test_longview_subscriptions_list()
    print(subscriptions_id)
    res = (
        exec_test_command(
            BASE_CMD
            + ["subscription-view", subscriptions_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["id", "label", "clients_included"]
    assert_headers_in_lines(headers, lines)

