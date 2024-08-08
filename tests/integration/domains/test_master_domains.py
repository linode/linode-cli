import re
import time

import pytest

from linodecli.exit_codes import ExitCodes

from tests.integration.helpers import (
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "domains"]


@pytest.fixture
def master_test_domain():
    timestamp = str(time.time_ns())
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

    yield master_domain_id

    delete_target_id(target="domains", id=master_domain_id)


def test_create_domain_fails_without_spcified_type():
    timestamp = str(time.time_ns())

    # get debug output from linode-cli to a temporary file..
    # not all output from the linode-cli goes to stdout, stderr

    result = exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--domain",
            "example.bc-" + timestamp + ".com",
            "--soa_email",
            "pthiel@linode.com",
            "--text",
            "--no-headers",
        ], expected_code=ExitCodes.UNRECOGNIZED_COMMAND
    ).stderr.decode()

    assert "Request failed: 400" in result
    assert "type is required" in result


def test_create_master_domain_fails_without_soa_email():
    timestamp = str(time.time_ns())
    result = exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--type",
            "master",
            "--domain",
            "example.bc-" + timestamp + ".com",
            "--text",
            "--no-headers",
        ], expected_code=ExitCodes.UNRECOGNIZED_COMMAND
    ).stderr.decode()

    assert "Request failed: 400" in result
    assert "soa_email	soa_email required when type=master" in result


@pytest.mark.smoke
def test_create_master_domain(master_domain):
    domain_id = master_domain
    assert re.search("[0-9]+", domain_id)


def test_update_master_domain_soa_email(master_test_domain):
    # Remove --master_ips param when 872 is resolved
    timestamp = str(time.time_ns())
    new_soa_email = "pthiel_new@linode.com"

    domain_id = master_test_domain

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


def test_list_master_domain(master_test_domain):
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


def test_show_domain_detail(master_test_domain):
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
