import logging
import re
import time

import pytest

from tests.integration.helpers import exec_test_command, remove_all

BASE_CMD = ["linode-cli", "firewalls", "rules-update"]
FIREWALL_LABEL = "example-firewall-label"


@pytest.fixture(scope="session", autouse=True)
def create_firewall():
    # Create one domain for some tests in this suite
    try:
        remove_all(target="firewalls")
        # Create domain
        firewall_id = (
            exec_test_command(
                [
                    "linode-cli",
                    "firewalls",
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
            .stdout.decode()
            .rstrip()
        )
    except:
        logging.exception("Failed creating domain in setup")

    yield firewall_id
    # teardown - delete all firewalls
    try:
        remove_all(target="firewalls")
    except:
        logging.exception("Failed to delete all firewalls")


def test_add_rule_to_existing_firewall(create_firewall):
    firewall_id = create_firewall
    inbound_rule = '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": "accept-inbound-SSH"}]'
    outbound_rule = '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.2/32"]}, "action": "ACCEPT", "label": "accept-outbound-SSH"}]'
    result = (
        exec_test_command(
            BASE_CMD
            + [
                firewall_id,
                "--inbound",
                inbound_rule,
                "--outbound",
                outbound_rule,
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    # search strings for assertion since output replaces all the double quotes in json with single quote
    ir_str = inbound_rule[1:-1].replace('"', "'")
    or_str = outbound_rule[1:-1].replace('"', "'")

    assert ir_str in result
    assert or_str in result


def test_add_multiple_rules(create_firewall):
    firewall_id = create_firewall
    inbound_rule_1 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": "accept-inbound-SSH"}'
    inbound_rule_2 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.2/32"]}, "action": "ACCEPT", "label": "accept-inbound-SSH-2"}'
    inbound_rules = "[" + inbound_rule_1 + "," + inbound_rule_2 + "]"
    result = (
        exec_test_command(
            BASE_CMD
            + [
                firewall_id,
                "--inbound",
                inbound_rules,
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert (
        inbound_rule_1.replace('"', "'")
        + " "
        + inbound_rule_2.replace('"', "'")
        in result
    )


def test_swap_rules():
    timestamp = str(int(time.time()))
    firewall_label = "label-fw-test" + timestamp
    inbound_rule_1 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": "swap_rule_1"}'
    inbound_rule_2 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.2/32"]}, "action": "ACCEPT", "label": "swap_rule_2"}'
    inbound_rules = "[" + inbound_rule_1 + "," + inbound_rule_2 + "]"
    firewall_id = (
        exec_test_command(
            [
                "linode-cli",
                "firewalls",
                "create",
                "--label",
                firewall_label,
                "--rules.outbound_policy",
                "ACCEPT",
                "--rules.inbound_policy",
                "DROP",
                "--rules.inbound",
                inbound_rules,
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    swapped_rules = "[" + inbound_rule_2 + "," + inbound_rule_1 + "]"

    # swapping rules
    result = (
        exec_test_command(
            BASE_CMD
            + [
                firewall_id,
                "--inbound",
                swapped_rules,
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert (
        inbound_rule_2.replace('"', "'")
        + " "
        + inbound_rule_1.replace('"', "'")
        in result
    )


def test_update_inbound_and_outbound_policy(create_firewall):
    firewall_id = create_firewall
    outbound_policy = "DROP"
    inbound_policy = "ACCEPT"
    result = (
        exec_test_command(
            BASE_CMD
            + [
                firewall_id,
                "--inbound_policy",
                inbound_policy,
                "--outbound_policy",
                outbound_policy,
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search(inbound_policy + "," + outbound_policy, result)


def test_remove_one_rule_via_rules_update():
    timestamp = str(int(time.time()))
    firewall_label = "label-fw-test" + timestamp
    inbound_rule_1 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": "test_rule_1"}'
    inbound_rule_2 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.2/32"]}, "action": "ACCEPT", "label": "rule_to_delete"}'
    inbound_rules = "[" + inbound_rule_1 + "," + inbound_rule_2 + "]"
    firewall_id = (
        exec_test_command(
            [
                "linode-cli",
                "firewalls",
                "create",
                "--label",
                firewall_label,
                "--rules.outbound_policy",
                "ACCEPT",
                "--rules.inbound_policy",
                "DROP",
                "--rules.inbound",
                inbound_rules,
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    new_rule = "[" + inbound_rule_1 + "]"
    # swapping rules
    result = (
        exec_test_command(
            BASE_CMD
            + [firewall_id, "--inbound", new_rule, "--text", "--no-headers"]
        )
        .stdout.decode()
        .rstrip()
    )

    assert inbound_rule_1.replace('"', "'") in result
    assert inbound_rule_2.replace('"', "'") not in result


def test_list_rules(create_firewall):
    firewall_id = create_firewall
    new_label = '"rules-list-test"'
    inbound_rule = (
        '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": '
        + new_label
        + "}]"
    )
    # adding a rule
    exec_test_command(
        BASE_CMD
        + [
            firewall_id,
            "--inbound",
            inbound_rule,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).stdout.decode().rstrip()
    result = (
        exec_test_command(
            [
                "linode-cli",
                "firewalls",
                "rules-list",
                firewall_id,
                "--text",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert new_label.replace('"', "'") in result
