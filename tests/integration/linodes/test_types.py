import pytest

from tests.integration.helpers import assert_headers_in_lines, exec_test_command


# verifying the DC pricing changes along with types
@pytest.mark.smoke
def test_linode_type():
    output = exec_test_command(
        ["linode-cli", "linodes", "types", "--text"]
    ).stdout.decode()

    headers = [
        "id",
        "label",
        "class",
        "disk",
        "memory",
        "vcpus",
        "gpus",
        "network_out",
        "transfer",
        "price.hourly",
        "price.monthly",
    ]

    assert_headers_in_lines(headers, output.splitlines())
