import os
import time
import re
import pytest
import logging

from tests.integration.helpers import exec_test_command, delete_all_domains


BASE_CMD = ["linode-cli", "events"]


@pytest.fixture(scope="session", autouse=True)
def events_setup():
    # Create one domain for some tests in this suite
    try:
        timestamp = str(int(time.time()))
        # Create domain
        domain_id = exec_test_command(['linode-cli', 'domains', 'create', '--type', 'master', '--domain', 'A'+timestamp + "example.com",
                                              '--soa_email=developer-test@linode.com', '--text', '--no-header', '--format', 'id']).stdout.decode().rstrip()

    except:
        logging.exception("Failed creating domain in setup")

    yield domain_id

    try:
        delete_all_domains()
    except:
        logging.exception("Failed to delete all domains")


def get_domain_id():
    process = exec_test_command(['linode-cli', 'domains', 'list', '--format=id', '--text', '--no-header'])
    output = process.stdout.decode()
    domain_id_arr = output.splitlines()
    return domain_id_arr[0]


def test_print_events_usage_information():
    process = exec_test_command(BASE_CMD)
    output = process.stdout.decode()

    assert("linode-cli events [ACTION]" in output)
    assert(re.search("mark-read.*Event Mark as Read", output))
    assert (re.search("mark-seen.*Event Mark as Seen", output))
    assert (re.search("list.*Events List", output))
    assert (re.search("view.*Event View", output))


def test_list_events():
    process = exec_test_command(BASE_CMD + ["list", "--text", "--no-headers", '--delimiter', ','])
    output = process.stdout.decode()

    assert (re.search("[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", output))


def test_view_events():
    event_id_arr = os.popen('linode-cli events list --format "id" --text --no-headers | xargs |  awk "{ print $1 }"').read().rstrip().split()
    event_id = event_id_arr[0]

    result = exec_test_command(BASE_CMD + ["view", event_id, '--text', '--no-headers', '--delimiter', ',']).stdout.decode()
    assert (re.search("[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", result))


def test_mark_event_seen():
    event_id_arr = os.popen('linode-cli events list --format "id" --text --no-headers | xargs |  awk "{ print $1 }"').read().rstrip().split()
    event_id = event_id_arr[0]

    # mark event as seen
    exec_test_command(BASE_CMD + ["mark-seen", event_id, '--text', '--no-headers', '--delimiter', ',']).stdout.decode()

    # view event
    result = exec_test_command(
        BASE_CMD + ["view", event_id, '--text', '--no-headers', '--delimiter', ',']).stdout.decode()
    assert (re.search("[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", result))


def test_mark_event_read():
    event_id_arr = os.popen('linode-cli events list --format "id" --text --no-headers | xargs |  awk "{ print $1 }"').read().rstrip().split()
    event_id = event_id_arr[0]

    # mark event as seen
    exec_test_command(BASE_CMD + ["mark-read", event_id, '--text', '--no-headers', '--delimiter', ',']).stdout.decode()

    # view event
    result = exec_test_command(
        BASE_CMD + ["view", event_id, '--text', '--no-headers', '--delimiter', ',']).stdout.decode()
    assert (re.search("[0-9]+,.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", result))


def test_filter_events_by_entity_id():
    event_id_arr = os.popen('linode-cli events list --format "id" --text --no-headers | xargs |  awk "{ print $1 }"').read().rstrip().split()
    event_id = event_id_arr[0]

    result = exec_test_command(BASE_CMD + ["list", '--id', event_id, '--text', '--no-headers', '--delimiter', ',']).stdout.decode()
    assert (re.search(event_id+",.*,.*,[0-9]+-[0-9][0-9]-.*,.*,[a-z]+.*", result))


def test_create_domain_and_filter_domain_events(events_setup):
    domain_id = events_setup
    result = exec_test_command(BASE_CMD+['list', '--entity.id', domain_id, '--entity.type', 'domain', '--text', '--no-headers', '--delimiter', ',']).stdout.decode()

    assert (re.search("[0-9]+,.*,domain_create,A[0-9]+.*,[0-9]+-[0-9][0-9]-.*,.*", result))
