import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_random_text,
)

FIREWALL_LABEL = "label-fw-test-" + get_random_text(5)


@pytest.fixture(scope="session")
def firewall_id():
    firewall_id = exec_test_command(
        BASE_CMDS["firewalls"]
        + [
            "create",
            "--label",
            FIREWALL_LABEL,
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

    yield firewall_id

    delete_target_id(target="firewalls", id=firewall_id)
