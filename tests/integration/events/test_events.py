import re

import pytest

from tests.integration.events.fixtures import (  # noqa: F401
    events_create_domain,
)
from tests.integration.helpers import BASE_CMDS, exec_test_command


def test_print_events_usage_information():
    output = exec_test_command(BASE_CMDS["events"])

    assert "linode-cli events [ACTION]" in output

    assert re.search(
        "mark-read.*(Event Mark as Read|Mark an event as read)", output
    )
    assert re.search(
        "mark-seen.*(Event Mark as Seen|Mark an event as seen)", output
    )
    assert re.search("list.*(Events List|List events)", output)
    assert re.search("view.*(Event View|Get an event)", output)


@pytest.mark.smoke
def test_list_events():
    output = exec_test_command(
        BASE_CMDS["events"]
        + ["list", "--text", "--no-headers", "--delimiter", ","]
    )

    assert re.search("[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", output)


def test_view_events():
    event_id = exec_test_command(
        BASE_CMDS["events"]
        + [
            "list",
            "--format",
            "id",
            "--no-headers",
            "--text",
        ]
    ).split()[0]

    result = exec_test_command(
        BASE_CMDS["events"]
        + ["view", event_id, "--text", "--no-headers", "--delimiter", ","]
    )
    assert re.search("[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", result)


def test_mark_event_seen():
    event_id = exec_test_command(
        BASE_CMDS["events"]
        + [
            "list",
            "--format",
            "id",
            "--no-headers",
            "--text",
        ]
    ).split()[0]

    # mark event as seen
    exec_test_command(
        BASE_CMDS["events"]
        + ["mark-seen", event_id, "--text", "--no-headers", "--delimiter", ","]
    )

    # view event
    result = exec_test_command(
        BASE_CMDS["events"]
        + ["view", event_id, "--text", "--no-headers", "--delimiter", ","]
    )
    assert re.search("[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", result)


@pytest.mark.smoke
def test_mark_event_read():
    event_id = exec_test_command(
        [
            "linode-cli",
            "events",
            "list",
            "--format",
            "id",
            "--no-headers",
            "--text",
        ]
    ).split()[0]

    # mark event as read
    exec_test_command(
        BASE_CMDS["events"]
        + ["mark-read", event_id, "--text", "--no-headers", "--delimiter", ","]
    )

    # view event
    result = exec_test_command(
        BASE_CMDS["events"]
        + ["view", event_id, "--text", "--no-headers", "--delimiter", ","]
    )
    assert re.search("[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", result)


def test_filter_events_by_entity_id():
    event_id = exec_test_command(
        [
            "linode-cli",
            "events",
            "list",
            "--format",
            "id",
            "--no-headers",
            "--text",
        ]
    ).split()[0]

    result = exec_test_command(
        BASE_CMDS["events"]
        + [
            "list",
            "--id",
            event_id,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    )
    assert re.search(
        event_id + ",.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", result
    )


def test_create_domain_and_filter_domain_events(events_create_domain):
    domain_id = events_create_domain
    output = exec_test_command(
        BASE_CMDS["events"]
        + [
            "list",
            "--entity.id",
            domain_id,
            "--entity.type",
            "domain",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    )

    assert "domain_create" in output
