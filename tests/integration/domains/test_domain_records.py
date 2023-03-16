import logging
import re
import time

import pytest

from tests.integration.helpers import (
    SUCCESS_STATUS_CODE,
    delete_all_domains,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "domains"]


@pytest.fixture(scope="session", autouse=True)
def domain_records_setup():
    # Create one domain for some tests in this suite
    try:
        timestamp = str(int(time.time()))
        # Create domain
        process = exec_test_command(
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
        output = process.stdout.decode()
        domain_id_arr = output.splitlines()

        # Create record
        exec_test_command(
            BASE_CMD
            + [
                "records-create",
                "--protocol=tcp",
                "--type=SRV",
                "--port=23",
                "--priority=4",
                "--service=telnet",
                "--target=8.8.8.8",
                "--weight=4",
                "--text",
                "--no-header",
                "--delimiter=,",
                domain_id_arr[0],
            ]
        )

    except:
        logging.exception("Failed creating domain in setup")

    yield "setup"

    try:
        delete_all_domains()
    except:
        logging.exception("Failed to delete all domains")


def get_domain_id():
    process = exec_test_command(
        BASE_CMD + ["list", "--format=id", "--text", "--no-header"]
    )
    output = process.stdout.decode()
    domain_id_arr = output.splitlines()
    return domain_id_arr[0]


def get_record_id(domain_id: str):
    process = exec_test_command(
        BASE_CMD
        + ["records-list", domain_id, "--format=id", "--text", "--no-header"]
    )
    output = process.stdout.decode()
    record_id_arr = output.splitlines()
    return record_id_arr[0]


def test_create_a_domain():
    timestamp = str(int(time.time()))

    # Current domain list
    process = exec_test_command(
        BASE_CMD + ["list", '--format="id"', "--text", "--no-header"]
    )
    output_current = process.stdout.decode()

    # Create domain
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
        ]
    )

    process = exec_test_command(
        BASE_CMD + ["list", "--format=id", "--text", "--no-header"]
    )
    output_after = process.stdout.decode()

    # Check if list is bigger than previous list
    assert (
        len(output_after.splitlines()) > len(output_current.splitlines()),
        "the list is not updated with new domain..",
    )


def test_create_domain_srv_record():
    process = exec_test_command(
        BASE_CMD + ["list", "--format=id", "--text", "--no-header"]
    )
    output = process.stdout.decode()

    domain_id_arr = output.splitlines()

    process = exec_test_command(
        BASE_CMD
        + [
            "records-create",
            "--protocol=tcp",
            "--type=SRV",
            "--port=23",
            "--priority=4",
            "--service=telnet",
            "--target=8.8.8.8",
            "--weight=4",
            "--text",
            "--no-header",
            "--delimiter=,",
            domain_id_arr[0],
        ]
    )

    output = process.stdout.decode()

    assert (
        re.search("[0-9]+,SRV,_telnet._tcp,8.8.8.8,0,4,4", output),
        "Output does not match the format",
    )


def test_list_srv_record():
    process = exec_test_command(
        BASE_CMD
        + [
            "records-list",
            get_domain_id(),
            "--text",
            "--no-header",
            "--delimiter=,",
        ]
    )
    output = process.stdout.decode()

    assert (
        re.search("[0-9]+,SRV,_telnet._tcp,8.8.8.8,0,4,4", output),
        "Output does not match the format",
    )


def test_view_domain_record():
    domain_id = get_domain_id()
    record_id = get_record_id(domain_id)

    process = exec_test_command(
        BASE_CMD
        + [
            "records-view",
            domain_id,
            record_id,
            "--target= 8.8.4.4",
            "--text",
            "--no-header",
            "--delimiter=,",
        ]
    )
    output = process.stdout.decode()

    assert (
        re.search("[0-9]+,SRV,_telnet._tcp,8.8.8.8,0,4,4", output),
        "Output does not match the format",
    )


def test_update_domain_record():
    domain_id = get_domain_id()
    record_id = get_record_id(domain_id)

    process = exec_test_command(
        BASE_CMD
        + [
            "records-update",
            domain_id,
            record_id,
            "--target= 8.8.4.4",
            "--text",
            "--no-header",
            "--delimiter=,",
        ]
    )
    output = process.stdout.decode()

    assert (
        re.search("[0-9]+,SRV,_telnet._tcp,8.8.8.8,0,4,4", output),
        "Output does not match the format",
    )


def test_delete_a_domain_record():
    domain_id = get_domain_id()
    record_id = get_record_id(domain_id)

    process = exec_test_command(
        BASE_CMD + ["records-delete", domain_id, record_id]
    )

    # Assert on status code returned from deleting domain
    assert process.returncode == SUCCESS_STATUS_CODE


def test_delete_all_domains():
    delete_all_domains()
