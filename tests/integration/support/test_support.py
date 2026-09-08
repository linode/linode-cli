import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
)
from tests.integration.linodes.helpers import create_linode

HEADERS = ["id", "summary", "opened_by", "opened", "description"]


@pytest.fixture
def support_test_linode_id(linode_cloud_firewall):
    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        booted=False,
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture
def get_ticket_id():
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

    yield ticket_ids[0]


@pytest.mark.skip(
    reason="Test skipped because it creates a support ticket on the account"
)
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
            "Testing ticket",
            "--text",
            "--no-headers",
        ]
    )


def test_tickets_list():
    res = exec_test_command(
        BASE_CMDS["tickets"] + ["list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    assert_headers_in_lines(HEADERS, lines)


def test_tickets_view(get_ticket_id):
    if not get_ticket_id:
        pytest.skip("No support tickets available to view.")

    ticket_id = get_ticket_id

    res = exec_test_command(
        BASE_CMDS["tickets"] + ["view", ticket_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    assert_headers_in_lines(HEADERS, lines)


@pytest.mark.skip(
    reason="Test skipped because ticket creation test is skipped as well"
)
def test_reply_support_ticket(get_ticket_id):
    ticket_id = get_ticket_id

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


def test_view_replies_support_ticket(get_ticket_id):
    if not get_ticket_id:
        pytest.skip("No support tickets available to view replies.")

    ticket_id = get_ticket_id
    res = exec_test_command(
        BASE_CMDS["tickets"] + ["replies", ticket_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["created_by", "created"]
    assert_headers_in_lines(headers, lines)
