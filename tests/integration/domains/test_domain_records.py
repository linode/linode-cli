import re
import time

import pytest

from tests.integration.helpers import (
    SUCCESS_STATUS_CODE,
    delete_target_id,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "domains"]


@pytest.fixture(scope="session", autouse=True)
def domain_records_setup():
    timestamp = str(int(time.time()))
    # Create domain
    domain_id = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--type",
                "master",
                "--domain",
                timestamp + "example.com",
                "--soa_email=pthiel@linode.com",
                "--text",
                "--no-header",
                "--format=id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    # Create record
    record_id = (
        exec_test_command(
            BASE_CMD
            + [
                "records-create",
                "--protocol=tcp",
                "--type=SRV",
                "--port=23",
                "--priority=4",
                "--service=telnet",
                "--target=record-setup",
                "--weight=4",
                "--text",
                "--no-header",
                "--delimiter=,",
                "--format=id",
                domain_id,
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield domain_id, record_id

    delete_target_id(target="domains", id=domain_id)


def test_create_a_domain(create_master_domain):
    # Current domain list
    process = exec_test_command(
        BASE_CMD + ["list", '--format="id"', "--text", "--no-header"]
    )
    output_current = process.stdout.decode()

    # Create domain
    domain_id = create_master_domain

    process = exec_test_command(
        BASE_CMD + ["list", "--format=id", "--text", "--no-header"]
    )
    output_after = process.stdout.decode()

    # Check if list is bigger than previous list
    assert (
        len(output_after.splitlines()) > len(output_current.splitlines()),
        "the list is not updated with new domain..",
    )


def test_create_domain_srv_record(domain_records_setup):
    domain_id = domain_records_setup[0]

    process = exec_test_command(
        BASE_CMD
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

    output = process.stdout.decode()

    assert (
        re.search("[0-9]+,SRV,_telnet._tcp,target-test-record+,0,4,4", output),
        "Output does not match the format",
    )


def test_list_srv_record(domain_records_setup):
    domain_id = domain_records_setup[0]
    process = exec_test_command(
        BASE_CMD
        + [
            "records-list",
            domain_id,
            "--text",
            "--no-header",
            "--delimiter=,",
        ]
    )
    output = process.stdout.decode()

    assert (
        re.search("[0-9]+,SRV,_telnet._tcp,record-setup+,0,4,4", output),
        "Output does not match the format",
    )


def test_view_domain_record(domain_records_setup):
    domain_id = domain_records_setup[0]
    record_id = domain_records_setup[1]

    process = exec_test_command(
        BASE_CMD
        + [
            "records-view",
            domain_id,
            record_id,
            "--text",
            "--no-header",
            "--delimiter=,",
        ]
    )
    output = process.stdout.decode()

    assert (
        re.search("[0-9]+,SRV,_telnet._tcp,record-setup+,0,4,4", output),
        "Output does not match the format",
    )


def test_update_domain_record(domain_records_setup):
    domain_id = domain_records_setup[0]
    record_id = domain_records_setup[1]

    process = exec_test_command(
        BASE_CMD
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
    output = process.stdout.decode()

    assert (
        re.search("[0-9]+,SRV,_telnet._tcp,record-setup-update+,0,4,4", output),
        "Output does not match the format",
    )


def test_delete_a_domain_record(domain_records_setup):
    domain_id = domain_records_setup[0]
    record_id = domain_records_setup[1]

    process = exec_test_command(
        BASE_CMD + ["records-delete", domain_id, record_id]
    )

    # Assert on status code returned from deleting domain
    assert process.returncode == SUCCESS_STATUS_CODE
