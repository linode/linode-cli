import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
    get_random_text,
)
from tests.integration.linodes.helpers import create_linode


@pytest.fixture
def support_test_linode_id(linode_cloud_firewall):
    label = "cli-" + get_random_text(5)

    linode_id = create_linode()

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


# this will create a support ticket on your account
@pytest.mark.skip(reason="this will create a support ticket")
def test_create_support_ticket(support_test_linode_id):
    linode_id = support_test_linode_id
    exec_test_command(
        BASE_CMDS["tickets"]
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
    res = exec_test_command(
        BASE_CMDS["tickets"] + ["list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["summary", "opened_by", "opened"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def tickets_id():
    res = exec_test_command(
        BASE_CMDS["tickets"]
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
    ticket_ids = res.splitlines()
    if not ticket_ids or ticket_ids == [""]:
        pytest.skip("No support tickets available to test.")
    first_id = ticket_ids[0]
    yield first_id


def test_tickets_view(tickets_id):
    if not tickets_id:
        pytest.skip("No support tickets available to view.")

    ticket_id = tickets_id
    res = exec_test_command(
        BASE_CMDS["tickets"] + ["view", ticket_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["summary", "opened_by", "opened"]
    assert_headers_in_lines(headers, lines)


@pytest.mark.skip(
    reason="Creation of tickets are skipped no way of currently testing this"
)
def test_reply_support_ticket(tickets_id):
    ticket_id = tickets_id
    exec_test_command(
        BASE_CMDS["tickets"]
        + [
            "reply",
            ticket_id,
            "--description",
            "test reply on the support ticket",
            "--text",
            "--no-headers",
        ]
    )


def test_view_replies_support_ticket(tickets_id):
    if not tickets_id:
        pytest.skip("No support tickets available to view replies.")

    ticket_id = tickets_id
    res = exec_test_command(
        BASE_CMDS["tickets"] + ["replies", ticket_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["created_by", "created"]
    assert_headers_in_lines(headers, lines)
