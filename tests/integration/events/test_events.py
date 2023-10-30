import re
import time

import pytest

from tests.integration.helpers import delete_target_id, exec_test_command

BASE_CMD = ["linode-cli", "events"]


@pytest.fixture
def events_test_domain_id():
    timestamp = str(int(time.time_ns()))
    # Create domain
    domain_id = (
        exec_test_command(
            [
                "linode-cli",
                "domains",
                "create",
                "--type",
                "master",
                "--domain",
                "A" + timestamp + "example.com",
                "--soa_email=developer-test@linode.com",
                "--text",
                "--no-header",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield domain_id

    delete_target_id(target="domains", id=domain_id)


def test_print_events_usage_information():
    process = exec_test_command(BASE_CMD)
    output = process.stdout.decode()

    assert "linode-cli events [ACTION]" in output
    assert re.search("mark-read.*Event Mark as Read", output)
    assert re.search("mark-seen.*Event Mark as Seen", output)
    assert re.search("list.*Events List", output)
    assert re.search("view.*Event View", output)


@pytest.mark.smoke
def test_list_events():
    process = exec_test_command(
        BASE_CMD + ["list", "--text", "--no-headers", "--delimiter", ","]
    )
    output = process.stdout.decode()

    assert re.search("[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", output)


def test_view_events():
    event_id = (
        exec_test_command(
            [
                "linode-cli",
                "events",
                "list",
                "--format",
                "id",
                "--no-headers",
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
        .split()[0]
    )

    result = exec_test_command(
        BASE_CMD
        + ["view", event_id, "--text", "--no-headers", "--delimiter", ","]
    ).stdout.decode()
    assert re.search("[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", result)


def test_mark_event_seen():
    event_id = (
        exec_test_command(
            [
                "linode-cli",
                "events",
                "list",
                "--format",
                "id",
                "--no-headers",
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
        .split()[0]
    )

    # mark event as seen
    exec_test_command(
        BASE_CMD
        + ["mark-seen", event_id, "--text", "--no-headers", "--delimiter", ","]
    ).stdout.decode()

    # view event
    result = exec_test_command(
        BASE_CMD
        + ["view", event_id, "--text", "--no-headers", "--delimiter", ","]
    ).stdout.decode()
    assert re.search("[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", result)


@pytest.mark.smoke
def test_mark_event_read():
    event_id = (
        exec_test_command(
            [
                "linode-cli",
                "events",
                "list",
                "--format",
                "id",
                "--no-headers",
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
        .split()[0]
    )

    # mark event as read
    exec_test_command(
        BASE_CMD
        + ["mark-read", event_id, "--text", "--no-headers", "--delimiter", ","]
    ).stdout.decode()

    # view event
    result = exec_test_command(
        BASE_CMD
        + ["view", event_id, "--text", "--no-headers", "--delimiter", ","]
    ).stdout.decode()
    assert re.search("[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", result)


def test_filter_events_by_entity_id():
    event_id = (
        exec_test_command(
            [
                "linode-cli",
                "events",
                "list",
                "--format",
                "id",
                "--no-headers",
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
        .split()[0]
    )

    result = exec_test_command(
        BASE_CMD
        + [
            "list",
            "--id",
            event_id,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()
    assert re.search(
        event_id + ",.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", result
    )


@pytest.mark.skip(reason="https://github.com/linode/linode-cli/issues/500")
def test_create_domain_and_filter_domain_events(events_test_domain_id):
    domain_id = events_test_domain_id
    result = exec_test_command(
        BASE_CMD
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
    ).stdout.decode()

    assert re.search(
        "[0-9]+,.*,domain_create,A[0-9]+.*,[0-9]+-[0-9][0-9]-.*,.*", result
    )
