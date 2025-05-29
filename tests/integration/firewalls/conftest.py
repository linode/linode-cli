import pytest

from tests.integration.helpers import (
    delete_target_id,
    exec_test_command,
    get_random_text,
)

BASE_CMD = ["linode-cli", "firewalls"]


@pytest.fixture(scope="function")
def _firewall_id_and_label():
    # generate a unique label
    label = "fw-" + get_random_text(5)
    # create it and capture the ID
    result = exec_test_command(
        BASE_CMD
        + [
            "create",
            "--label",
            label,
            "--rules.outbound_policy",
            "ACCEPT",
            "--rules.inbound_policy",
            "DROP",
            "--text",
            "--no-headers",
            "--format",
            "id",
        ]
    )
    fw_id = result.stdout.decode().strip()
    yield fw_id, label
    # cleanup
    delete_target_id(target="firewalls", id=fw_id)


@pytest.fixture(scope="function")
def test_firewall_id(_firewall_id_and_label):
    """Only the ID, so old tests keep working."""
    return _firewall_id_and_label[0]


@pytest.fixture(scope="function")
def test_firewall_label(_firewall_id_and_label):
    """Only the label, for tests that need it explicitly."""
    return _firewall_id_and_label[1]
