import os
import re

import pytest

from tests.integration.domains.fixtures import (  # noqa: F401
    slave_domain,
)
from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
    get_random_text,
)


def test_create_slave_domain_fails_without_master_dns_server():
    os.system(
        'linode-cli domains create --type slave --domain "'
        + get_random_text(5)
        + '-example.com" --text --no-header 2>&1 | tee /tmp/test.txt'
    )
    result = exec_test_command(["cat", "/tmp/test.txt"])

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
        BASE_CMDS["domains"] + ["list", "--text", "--no-header"]
    )
    assert "-example.com" in result


def test_update_slave_domain(slave_domain):
    domain_id = slave_domain
    output = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "update",
            "--type",
            "slave",
            "--master_ips",
            "8.8.8.8",
            domain_id,
            "--text",
            "--no-header",
            "--delimiter=,",
        ]
    )

    assert "slave,active" in output
    assert domain_id in output
