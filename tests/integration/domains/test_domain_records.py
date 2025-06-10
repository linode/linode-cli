import re
import time

import pytest

from tests.integration.domains.fixtures import (  # noqa: F401
    domain_and_record,
    master_domain,
    slave_domain,
)
from tests.integration.helpers import (
    BASE_CMDS,
    contains_at_least_one_of,
    exec_test_command,
)


@pytest.mark.smoke
def test_create_a_domain(master_domain):
    # Current domain list
    domain_list_before = exec_test_command(
        BASE_CMDS["domains"]
        + ["list", '--format="id"', "--text", "--no-header"]
    )

    timestamp = str(time.time_ns())

    # Create domain
    another_domain = exec_test_command(
        [
            "linode-cli",
            "domains",
            "create",
            "--type",
            "master",
            "--domain",
            timestamp + "example.com",
            "--soa_email",
            "pthiel_test@linode.com",
            "--text",
            "--no-header",
            "--format",
            "id",
        ]
    )

    domain_list_after = exec_test_command(
        BASE_CMDS["domains"] + ["list", "--format=id", "--text", "--no-header"]
    )
    # Check if list is bigger than previous list
    assert len(domain_list_after.splitlines()) > len(
        domain_list_before.splitlines()
    )
    assert another_domain in domain_list_after


@pytest.mark.smoke
def test_create_domain_srv_record(domain_and_record):
    domain_id = domain_and_record[0]

    output = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "records-create",
            "--protocol=tcp",
            "--type=SRV",
            "--port=23",
            "--priority=4",
            "--service=telnet",
            "--target=target-test-record",
            "--weight=4",
            "--text",
            "--no-header",
            "--delimiter=,",
            domain_id,
        ]
    )

    assert re.search(
        r"[0-9]+,SRV,_telnet\._tcp,target-test-record\.\w+-example\.com,0,4,4",
        str(output),
    )


def test_list_srv_record(domain_and_record):
    domain_id = domain_and_record[0]
    output = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "records-list",
            domain_id,
            "--text",
            "--no-header",
            "--delimiter=,",
        ]
    )

    assert re.search(
        r"[0-9]+,SRV,_telnet\._tcp,record-setup\.\w+-example\.com,0,4,4",
        str(output),
    )


@pytest.mark.smoke
def test_view_domain_record(domain_and_record):
    domain_id = domain_and_record[0]
    record_id = domain_and_record[1]

    output = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "records-view",
            domain_id,
            record_id,
            "--text",
            "--no-header",
            "--delimiter=,",
        ]
    )

    assert re.search(
        r"[0-9]+,SRV,_telnet\._tcp,record-setup\.\w+-example\.com,0,4,4",
        output,
    )


def test_update_domain_record(domain_and_record):
    domain_id = domain_and_record[0]
    record_id = domain_and_record[1]

    output = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "records-update",
            domain_id,
            record_id,
            "--target=record-setup-update",
            "--text",
            "--no-header",
            "--delimiter=,",
        ]
    )

    assert re.search(
        r"[0-9]+,SRV,_telnet\._tcp,record-setup-update\.\w+-example\.com,0,4,4",
        str(output),
    )


def test_delete_a_domain_record(domain_and_record):
    domain_id = domain_and_record[0]
    record_id = domain_and_record[1]

    exec_test_command(
        BASE_CMDS["domains"] + ["records-delete", domain_id, record_id]
    )


def test_help_records_list(domain_and_record):
    output = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "records-list",
            "--help",
        ]
    )

    assert contains_at_least_one_of(
        output, ["List domain records", "Domain Records List"]
    )
    assert "You may filter results with:" in output
    assert "--type" in output
    assert "--name" in output
    assert "--target" in output
    assert "--tag" in output
