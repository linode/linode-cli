import time

import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
)


@pytest.fixture
def master_domain():
    timestamp = str(time.time_ns())

    domain_id = exec_test_command(
        BASE_CMDS["domains"]
        + [
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

    yield domain_id

    delete_target_id("domains", id=domain_id)


@pytest.fixture
def slave_domain():
    timestamp = str(time.time_ns())

    domain_id = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "create",
            "--type",
            "slave",
            "--domain",
            timestamp + "-example.com",
            "--master_ips",
            "1.1.1.1",
            "--text",
            "--no-header",
            "--delimiter",
            ",",
            "--format=id",
        ]
    )

    yield domain_id

    delete_target_id("domains", domain_id)


@pytest.fixture
def test_domain_and_record():
    timestamp = str(time.time_ns())
    # Create domain
    domain_id = exec_test_command(
        BASE_CMDS["domains"]
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

    # Create record
    record_id = exec_test_command(
        BASE_CMDS["domains"]
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

    yield domain_id, record_id

    delete_target_id(target="domains", id=domain_id)
