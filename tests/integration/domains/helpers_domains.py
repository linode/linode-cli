import time

import pytest

from tests.integration.helpers import delete_target_id, exec_test_command

BASE_CMD = ["linode-cli", "domains"]


# test helper specific to domain test suite
@pytest.fixture
def create_master_domain():
    timestamp = str(int(time.time()))

    domain_id = (
        exec_test_command(
            BASE_CMD
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
        .stdout.decode()
        .rstrip()
    )

    yield domain_id

    delete_target_id("domains", id=domain_id)


# test helper specific to domain test suite
@pytest.fixture
def create_slave_domain():
    timestamp = str(int(time.time()))

    domain_id = (
        exec_test_command(
            BASE_CMD
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
        .stdout.decode()
        .rstrip()
    )

    yield domain_id

    delete_target_id("domains", domain_id)
