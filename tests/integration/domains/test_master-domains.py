import logging
import os
import re
import time

import pytest

from tests.integration.helpers import (
    FAILED_STATUS_CODE,
    delete_all_domains,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "domains"]


@pytest.fixture(scope="session", autouse=True)
def setup_master_domains():
    timestamp = str(int(time.time()))
    # create one master domain for some tests in this suite
    try:
        # Create domain
        master_domain_id = (
            exec_test_command(
                BASE_CMD
                + [
                    "create",
                    "--type",
                    "master",
                    "--domain",
                    "BC" + timestamp + "-example.com",
                    "--soa_email=pthiel" + timestamp + "@linode.com",
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
    except:
        logging.exception("Failed to create master domain in setup")
    yield master_domain_id
    try:
        delete_all_domains()
    except:
        logging.exception("Failed to delete all domains")


def test_create_domain_fails_without_spcified_type():
    timestamp = str(int(time.time()))

    # get debug output from linode-cli to a temporary file..
    # not all output from the linode-cli goes to stdout, stderr
    os.system(
        'linode-cli domains create \
    --domain "BC'
        + timestamp
        + '-example.com" \
    --soa_email="pthiel@linode.com" \
    --text \
    --no-header 2>&1 | tee /tmp/test.txt'
    )

    status = os.system(
        'linode-cli domains create \
    --domain "BC'
        + timestamp
        + '-example.com" \
    --soa_email="pthiel@linode.com" \
    --text \
    --no-header'
    )

    result = exec_test_command(["cat", "/tmp/test.txt"]).stdout.decode()

    assert status == FAILED_STATUS_CODE
    assert "Request failed: 400" in result
    assert "type is required" in result


def test_create_master_domain_fails_without_soa_email():
    timestamp = str(int(time.time()))

    os.system(
        'linode-cli domains create \
            --type master \
            --domain "BC$'
        + timestamp
        + '-example.com" \
            --text \
            --no-header 2>&1 | tee /tmp/test.txt'
    )

    status = os.system(
        'linode-cli domains create \
    --type master \
    --domain "BC$'
        + timestamp
        + '-example.com" \
    --text \
    --no-header'
    )

    result = exec_test_command(["cat", "/tmp/test.txt"]).stdout.decode()

    assert status == FAILED_STATUS_CODE
    assert "Request failed: 400" in result
    assert "soa_email	soa_email required when type=master" in result


def test_create_master_domain():
    timestamp = str(int(time.time()))

    result = exec_test_command(
        BASE_CMD
        + [
            "create",
            "--type",
            "master",
            "--domain",
            "BC" + timestamp + "-example.com",
            "--soa_email=pthiel" + timestamp + "@linode.com",
            "--text",
            "--no-header",
            "--delimiter",
            ",",
            "--format=id,domain,type,status,soa_email",
        ]
    ).stdout.decode()

    assert re.search(
        "[0-9]+,BC"
        + timestamp
        + "-example.com,master,active,pthiel"
        + timestamp
        + "@linode.com",
        result,
    )


def test_update_master_domain_soa_email(setup_master_domains):
    # Remove --master_ips param when 872 is resolved
    timestamp = str(int(time.time()))
    new_soa_email = "pthiel_new@linode.com"

    domain_id = setup_master_domains

    result = exec_test_command(
        BASE_CMD
        + [
            "update",
            domain_id,
            "--type",
            "master",
            "--master_ips",
            "8.8.8.8",
            "--soa_email",
            new_soa_email,
            "--format=soa_email",
            "--text",
            "--no-header",
        ]
    ).stdout.decode()

    assert new_soa_email in result


def test_list_master_domain(setup_master_domains):
    result = exec_test_command(
        BASE_CMD
        + [
            "list",
            "--format=id,domain,type,status",
            "--text",
            "--no-header",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()

    assert re.search("[0-9]+,BC[0-9]+-example.com,master,active", result)


def test_show_domain_detail(setup_master_domains):
    result = exec_test_command(
        BASE_CMD
        + [
            "list",
            "--format=id,domain,type,status",
            "--text",
            "--no-header",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()

    assert re.search("[0-9]+,BC[0-9]+-example.com,master,active", result)


# This test actually gets covered by the teardown method in @fixture
def test_delete_all_master_domains():
    delete_all_domains()
