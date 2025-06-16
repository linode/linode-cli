import json
import re

from tests.integration.firewalls.fixtures import (  # noqa: F401
    firewall_id,
)

def test_add_rule_to_existing_firewall(firewall_id):
    firewall_id = firewall_id
    inbound_rule = '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": "accept-inbound-SSH"}]'
    outbound_rule = '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.2/32"]}, "action": "ACCEPT", "label": "accept-outbound-SSH"}]'
    result = json.loads(
        exec_test_command(
            BASE_CMDS["firewalls"]
            + [
                "rules-update",
                firewall_id,
                "--inbound",
                inbound_rule,
                "--outbound",
                outbound_rule,
                "--json",
            ]
        )
    )

    assert result[0]["inbound"][0] == json.loads(inbound_rule)[0]
    assert result[0]["outbound"][0] == json.loads(outbound_rule)[0]


def test_add_multiple_rules(firewall_id):
    firewall_id = firewall_id
    inbound_rule_1 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": "accept-inbound-SSH"}'
    inbound_rule_2 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.2/32"]}, "action": "ACCEPT", "label": "accept-inbound-SSH-2"}'
    inbound_rules = "[" + inbound_rule_1 + "," + inbound_rule_2 + "]"
    result = json.loads(
        exec_test_command(
            BASE_CMDS["firewalls"]
            + [
                "rules-update",
                firewall_id,
                "--inbound",
                inbound_rules,
                "--json",
            ]
        )
    )

    assert result[0]["inbound"][0] == json.loads(inbound_rule_1)
    assert result[0]["inbound"][1] == json.loads(inbound_rule_2)


def test_swap_rules():
    firewall_label = "label-fw-test" + get_random_text(5)
    inbound_rule_1 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": "swap_rule_1"}'
    inbound_rule_2 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.2/32"]}, "action": "ACCEPT", "label": "swap_rule_2"}'
    inbound_rules = "[" + inbound_rule_1 + "," + inbound_rule_2 + "]"
    firewall_id = exec_test_command(
        BASE_CMDS["firewalls"]
        + [
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

    swapped_rules_obj = list(reversed(inbound_rules_obj))
    swapped_rules = json.dumps(swapped_rules_obj)

    result = json.loads(
        exec_test_command(
            BASE_CMDS["firewalls"]
            + [
                "rules-update",
                firewall_id,
                "--inbound",
                swapped_rules,
                "--json",
            ]
        )
    )

    assert result[0]["inbound"][0] == swapped_rules_obj[0]
    assert result[0]["inbound"][1] == swapped_rules_obj[1]

    delete_target_id(target="firewalls", id=firewall_id)


def test_update_inbound_and_outbound_policy(firewall_id):
    firewall_id = firewall_id
    outbound_policy = "DROP"
    inbound_policy = "ACCEPT"
    result = exec_test_command(
        BASE_CMDS["firewalls"]
        + [
            "rules-update",
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

    assert re.search(inbound_policy + "," + outbound_policy, result)


def test_remove_one_rule_via_rules_update():
    firewall_label = "label-fw-test" + get_random_text(5)
    inbound_rule_1 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": "test_rule_1"}'
    inbound_rule_2 = '{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.2/32"]}, "action": "ACCEPT", "label": "rule_to_delete"}'
    inbound_rules = "[" + inbound_rule_1 + "," + inbound_rule_2 + "]"
    firewall_id = exec_test_command(
        BASE_CMDS["firewalls"]
        + [
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

    new_rule = "[" + inbound_rule_1 + "]"
    # swapping rules
    result = json.loads(
        exec_test_command(
            BASE_CMDS["firewalls"]
            + [
                "rules-update",
                firewall_id,
                "--inbound",
                new_rule,
                "--json",
                "--no-headers",
            ]
        )
    )

    rule_labels = [v["label"] for v in result[0]["inbound"]]
    assert "test_rule_1" in rule_labels
    assert "rule_to_delete" not in rule_labels

    delete_target_id(target="firewalls", id=firewall_id)


def test_list_rules(firewall_id):
    firewall_id = firewall_id
    new_label = '"rules-list-test"'
    inbound_rule = (
        '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": '
        + new_label
        + "}]"
    )
    # adding a rule
    exec_test_command(
        BASE_CMDS["firewalls"]
        + [
            "rules-update",
            firewall_id,
            "--inbound",
            inbound_rule,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    )
    result = exec_test_command(
        BASE_CMDS["firewalls"]
        + [
            "rules-list",
            firewall_id,
            "--text",
            "--no-headers",
        ]
    )

    assert new_label.replace('"', "") in result


def test_list_rules_json(firewall_id):
    firewall_id = firewall_id
    new_label = '"rules-list-test"'
    inbound_rule = (
        '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": '
        + new_label
        + "}]"
    )
    # adding a rule
    exec_test_command(
        BASE_CMDS["firewalls"]
        + [
            "rules-update",
            firewall_id,
            "--inbound",
            inbound_rule,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    )
    result = json.loads(
        exec_test_command(
            BASE_CMDS["firewalls"]
            + [
                "rules-list",
                firewall_id,
                "--json",
            ]
        )
    )

    assert result[0]["inbound"][0]["action"] == "ACCEPT"
    assert result[0]["inbound"][0]["label"] == "rules-list-test"
    assert result[0]["inbound"][0]["addresses"]["ipv4"] == ["198.0.0.1/32"]


def test_list_rules_json_format(firewall_id):
    firewall_id = firewall_id
    new_label = '"rules-list-test"'
    inbound_rule = (
        '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": '
        + new_label
        + "}]"
    )
    # adding a rule
    exec_test_command(
        BASE_CMDS["firewalls"]
        + [
            "rules-update",
            firewall_id,
            "--inbound",
            inbound_rule,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    )
    result = json.loads(
        exec_test_command(
            BASE_CMDS["firewalls"]
            + [
                "rules-list",
                firewall_id,
                "--json",
                "--format",
                "label",
            ]
        )
    )
    assert result[0]["inbound"][0]["label"] == "rules-list-test"
