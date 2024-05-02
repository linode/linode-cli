import pytest

from tests.integration.helpers import assert_headers_in_lines, exec_test_command

BASE_CMD = ["linode-cli", "tickets"]


# this will create a support ticket on your account
def test_create_support_ticket(linode_with_label):
    linode_id = linode_with_label[1]
    exec_test_command(
        BASE_CMD
        + [
            "create",
            "--description",
            "Creating support ticket for test verification",
            "--linode_id",
            linode_id,
            "--summary",
            "Testing ticket" "--text",
            "--no-headers",
        ]
    )


def test_tickets_list():
    res = (
        exec_test_command(BASE_CMD + ["list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["summary", "opened_by", "opened"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def get_ticket_id():
    ticket_ids = (
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
        .split(",")
    )
    first_id = ticket_ids[0]
    yield first_id


def test_tickets_view(get_ticket_id):
    ticket_id = get_ticket_id
    res = (
        exec_test_command(
            BASE_CMD + ["view", ticket_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["summary", "opened_by", "opened"]
    assert_headers_in_lines(headers, lines)


def test_reply_support_ticket(get_ticket_id):
    ticket_id = get_ticket_id
    exec_test_command(
        BASE_CMD
        + [
            "reply",
            ticket_id,
            "--description",
            "test reply on the support ticket",
            "--text",
            "--no-headers",
        ]
    )


def test_view_replies_support_ticket(get_ticket_id):
    ticket_id = get_ticket_id
    res = (
        exec_test_command(
            BASE_CMD + ["replies", ticket_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["created_by", "created"]
    assert_headers_in_lines(headers, lines)
