import time

import pytest

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
    headers = ["id", "label", "created"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def test_client_id():
    client_id = (
        exec_test_command(
            BASE_CMD
            + [
                "list",
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
    first_id = client_id[0]
    yield first_id


def test_client_view(test_client_id):
    client_id = test_client_id
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


def test_update_longview_client_list(test_client_id):
    client_id = test_client_id
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
    headers = ["id", "label", "clients_included"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def test_subscriptions_id():
    subscriptions_id = (
        exec_test_command(
            BASE_CMD
            + [
                "subscriptions-list",
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
    first_id = subscriptions_id[0]
    yield first_id


def test_longview_subscriptions_list_view(test_subscriptions_id):
    subscriptions_id = test_subscriptions_id
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
