import re

import pytest

from tests.integration.helpers import delete_target_id, exec_test_command
from tests.integration.linodes.helpers_linodes import create_linode_and_wait

BASE_CMD = ["linode-cli", "networking"]


@pytest.fixture(scope="package")
def setup_test_networking():
    linode_id = create_linode_and_wait()

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


def test_display_ips_for_available_linodes(setup_test_networking):
    result = exec_test_command(
        BASE_CMD + ["ips-list", "--text", "--no-headers", "--delimiter", ","]
    ).stdout.decode()

    assert re.search("^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", result)
    assert re.search(
        "ipv4,True,[0-9]{1,3}\-[0-9]{1,3}\-[0-9]{1,3}\-[0-9]{1,3}\.ip.linodeusercontent.com,.*,[0-9][0-9][0-9][0-9][0-9][0-9][0-9]*",
        result,
    )
    assert re.search("ipv6,True,,.*,[0-9][0-9][0-9][0-9][0-9][0-9]*", result)
    assert re.search(
        "(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))",
        result,
    )


@pytest.mark.smoke
def test_view_an_ip_address(setup_test_networking):
    linode_id = setup_test_networking
    linode_ipv4 = exec_test_command(
        [
            "linode-cli",
            "linodes",
            "view",
            linode_id,
            "--format",
            "ipv4",
            "--text",
            "--no-headers",
        ]
    ).stdout.rstrip()

    result = exec_test_command(
        BASE_CMD
        + [
            "ip-view",
            "--region",
            "us-east",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            linode_ipv4,
        ]
    ).stdout.decode()

    assert re.search("^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", result)


def test_allocate_additional_private_ipv4_address(setup_test_networking):
    linode_id = setup_test_networking

    result = exec_test_command(
        BASE_CMD
        + [
            "ip-add",
            "--type",
            "ipv4",
            "--linode_id",
            linode_id,
            "--delimiter",
            ",",
            "--public",
            "false",
            "--text",
            "--no-headers",
        ]
    ).stdout.decode()

    assert re.search("^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", result)
    assert re.search(
        "ipv4,False,.*,[0-9][0-9][0-9][0-9][0-9][0-9][0-9]*", result
    )
