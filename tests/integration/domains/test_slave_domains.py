import os
import re
import time

import pytest

from tests.integration.helpers import (
    FAILED_STATUS_CODE,
    SUCCESS_STATUS_CODE,
    delete_target_id,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "domains"]
timestamp = str(time.time_ns())


@pytest.fixture
def slave_domain_setup():
    # Create domain
    slave_domain_id = (
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

    yield slave_domain_id

    delete_target_id(target="domains", id=slave_domain_id)


def test_create_slave_domain_fails_without_master_dns_server():
    os.system(
        'linode-cli domains create --type slave --domain "'
        + timestamp
        + '-example.com" --text --no-header 2>&1 | tee /tmp/test.txt'
    )
    result = exec_test_command(["cat", "/tmp/test.txt"]).stdout.decode()

    assert "Request failed: 400" in result
    assert (
        "master_ips	You need at least one master DNS server IP address for this zone."
        in result
    )


@pytest.mark.smoke
def test_create_slave_domain(slave_domain):
    domain_id = slave_domain
    assert re.search("[0-9]+", domain_id)


def test_list_slave_domain(slave_domain):
    result = exec_test_command(
        BASE_CMD + ["list", "--text", "--no-header"]
    ).stdout.decode()
    assert "-example.com" in result


@pytest.mark.skip(reason="BUG 872")
def test_update_domain_fails_without_type(slave_domain_setup):
    domain_id = slave_domain_setup

    result = os.system(
        "linode-cli domains update "
        + domain_id
        + ' --master_ips 8.8.8.8 --text --no-header --deleteimiter "," --format "id,domain,type,status"'
    )

    assert result == FAILED_STATUS_CODE


def test_update_slave_domain(slave_domain_setup):
    domain_id = slave_domain_setup
    result = exec_test_command(
        BASE_CMD
        + [
            "update",
            "--type",
            "slave",
            "--master_ips",
            "8.8.8.8",
            domain_id,
            "--text",
            "--no-header",
        ]
    )

    assert result.returncode == SUCCESS_STATUS_CODE
