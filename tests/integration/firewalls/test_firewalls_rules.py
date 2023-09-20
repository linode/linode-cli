import json
import re
import time

import pytest

from tests.integration.helpers import delete_target_id, exec_test_command

BASE_CMD = ["linode-cli", "firewalls", "rules-update"]
FIREWALL_LABEL = "label-fw-test" + str(int(time.time()))


@pytest.fixture
def create_firewall():
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

    yield firewall_id
    # teardown - delete all firewalls
    delete_target_id(target="firewalls", id=firewall_id)


def test_add_rule_to_existing_firewall(create_firewall):
    firewall_id = create_firewall
    inbound_rule = '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": "accept-inbound-SSH"}]'
    outbound_rule = '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.2/32"]}, "action": "ACCEPT", "label": "accept-outbound-SSH"}]'
    result = json.loads(
        exec_test_command(
            BASE_CMD
            + [
                firewall_id,
                "--inbound",
                inbound_rule,
                "--outbound",
                outbound_rule,
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert result[0]["inbound"][0] == json.loads(inbound_rule)[0]
    assert result[0]["outbound"][0] == json.loads(outbound_rule)[0]


def test_add_multiple_rules(create_firewall):
    firewall_id = create_firewall
    inbound_rule_1 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": "accept-inbound-SSH"}'
    inbound_rule_2 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.2/32"]}, "action": "ACCEPT", "label": "accept-inbound-SSH-2"}'
    inbound_rules = "[" + inbound_rule_1 + "," + inbound_rule_2 + "]"
    result = json.loads(
        exec_test_command(
            BASE_CMD + [firewall_id, "--inbound", inbound_rules, "--json"]
        )
        .stdout.decode()
        .rstrip()
    )

    assert result[0]["inbound"][0] == json.loads(inbound_rule_1)
    assert result[0]["inbound"][1] == json.loads(inbound_rule_2)


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
    result = json.loads(
        exec_test_command(
            BASE_CMD
            + [
                firewall_id,
                "--inbound",
                swapped_rules,
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert result[0]["inbound"][0] == json.loads(inbound_rule_2)
    assert result[0]["inbound"][1] == json.loads(inbound_rule_1)

    delete_target_id(target="firewalls", id=firewall_id)


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
    result = json.loads(
        exec_test_command(
            BASE_CMD
            + [firewall_id, "--inbound", new_rule, "--json", "--no-headers"]
        )
        .stdout.decode()
        .rstrip()
    )

    rule_labels = [v["label"] for v in result[0]["inbound"]]
    assert "test_rule_1" in rule_labels
    assert "rule_to_delete" not in rule_labels

    delete_target_id(target="firewalls", id=firewall_id)


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

    assert new_label.replace('"', "") in result


def test_list_rules_json(create_firewall):
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
    result = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "firewalls",
                "rules-list",
                firewall_id,
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert result[0]["inbound"][0]["action"] == "ACCEPT"
    assert result[0]["inbound"][0]["label"] == "rules-list-test"
    assert result[0]["inbound"][0]["addresses"]["ipv4"] == ["198.0.0.1/32"]
