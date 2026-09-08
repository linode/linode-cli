import json

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


@pytest.fixture(scope="session")
def firewall_protocol_all():
    firewall_id = exec_test_command(
        BASE_CMDS["firewalls"]
        + [
            "create",
            "--label",
            "fw-test-" + get_random_text(5),
            "--rules.outbound_policy",
            "ACCEPT",
            "--rules.outbound",
            '[{"protocol": "ALL", "addresses": {"ipv4": ["198.51.100.0/24"]}, "action": "ACCEPT", "label": "protocol_ALL_test"}]',
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


@pytest.fixture(scope="session")
def firewall_protocol_numeric_and_all():
    response = json.loads(
        exec_test_command(
            BASE_CMDS["firewalls"]
            + [
                "create",
                "--label",
                "fw-test-" + get_random_text(5),
                "--rules.inbound_policy",
                "DROP",
                "--rules.inbound",
                '[{"protocol": "ALL", "addresses": {"ipv4": ["0.0.0.0/0"]}, "action": "ACCEPT", "label": "protocol_ALL_test"}]',
                "--rules.outbound_policy",
                "ACCEPT",
                "--rules.outbound",
                '[{"protocol": "40", "addresses": {"ipv4": ["198.51.100.0/24"]}, "action": "ACCEPT", "label": "protocol_numeric_test"}, '
                '{"protocol": "ALL", "addresses": {"ipv4": ["0.0.0.0/0"]}, "action": "ACCEPT", "label": "protocol_ALL_test"}]',
                "--json",
            ]
        )
    )

    yield response

    delete_target_id(target="firewalls", id=str(response[0]["id"]))
