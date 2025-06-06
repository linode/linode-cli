import json
import re
import time

import pytest
from pytest import MonkeyPatch

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
)

BASE_CMD = ["linode-cli", "firewalls"]
FIREWALL_LABEL = "fw-" + get_random_text(5)


@pytest.fixture
def test_firewall_id():
    firewall_id = (
        exec_test_command(
            BASE_CMD
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
        .stdout.decode()
        .rstrip()
    )

    yield firewall_id

    delete_target_id(target="firewalls", id=firewall_id)


@pytest.mark.smoke
def test_view_firewall(test_firewall_id):
    firewall_id = test_firewall_id

    result = (
        exec_test_command(
            BASE_CMD
            + [
                "view",
                firewall_id,
                "--no-headers",
                "--text",
                "--delimiter",
                ",",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search(firewall_id + "," + FIREWALL_LABEL + ",enabled", result)


def test_list_firewall(test_firewall_id):
    firewall_id = test_firewall_id

    result = (
        exec_test_command(
            BASE_CMD + ["list", "--no-headers", "--text", "--delimiter", ","]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search(firewall_id + "," + FIREWALL_LABEL + ",enabled", result)


@pytest.mark.smoke
def test_create_firewall_with_minimum_required_args():
    timestamp = str(time.time_ns())
    firewall_label = "label-fw-test" + timestamp
    result = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                firewall_label,
                "--rules.outbound_policy",
                "ACCEPT",
                "--rules.inbound_policy",
                "DROP",
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search("[0-9]+," + firewall_label + ",enabled", result)

    res_arr = result.split(",")
    firewall_id = res_arr[0]
    delete_target_id(target="firewalls", id=firewall_id)


def test_fails_to_create_firewall_without_inbound_policy():
    timestamp = str(time.time_ns())
    firewall_label = "fw_label" + timestamp
    result = (
        exec_failing_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                firewall_label,
                "--rules.outbound_policy",
                "ACCEPT",
                "--text",
                "--no-headers",
                "--format",
                "id",
            ],
            ExitCodes.REQUEST_FAILED,
        )
        .stderr.decode()
        .rstrip()
    )

    assert "inbound_policy is required" in result


def test_fails_to_create_firewall_without_outbound_policy():
    timestamp = str(time.time_ns())
    firewall_label = "fw_label" + timestamp
    result = (
        exec_failing_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                firewall_label,
                "--rules.inbound_policy",
                "DROP",
                "--text",
                "--no-headers",
                "--format",
                "id",
            ],
            ExitCodes.REQUEST_FAILED,
        )
        .stderr.decode()
        .rstrip()
    )

    assert "outbound_policy is required" in result


def test_firewall_label_must_be_unique_upon_creation(test_firewall_id):
    result = (
        exec_failing_test_command(
            BASE_CMD
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
            ],
            ExitCodes.REQUEST_FAILED,
        )
        .stderr.decode()
        .rstrip()
    )

    assert "Label must be unique among your Cloud Firewalls" in result


def test_create_firewall_with_inbound_and_outbound_args():
    timestamp = str(time.time_ns())
    firewall_label = "label-fw-test" + timestamp
    result = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                firewall_label,
                "--rules.outbound_policy",
                "ACCEPT",
                "--rules.inbound_policy",
                "DROP",
                "--rules.inbound",
                '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.2/32"]}, "action": "ACCEPT", "label": "accept-inbound-SSH"}]',
                "--rules.outbound",
                '[{"ports": "22", "protocol": "TCP", "addresses": {"ipv4": ["198.0.0.1/32"]}, "action": "ACCEPT", "label": "accept-outbound-SSH"}]',
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search("[0-9]+," + firewall_label + ",enabled", result)

    res_arr = result.split(",")
    firewall_id = res_arr[0]
    delete_target_id(target="firewalls", id=firewall_id)


def test_update_firewall(test_firewall_id):
    timestamp = str(time.time_ns())
    firewall_id = test_firewall_id
    updated_tag = "updated-tag" + timestamp
    updated_label = "updated-" + timestamp

    result = (
        exec_test_command(
            BASE_CMD
            + [
                "update",
                firewall_id,
                "--tags",
                updated_tag,
                "--label",
                updated_label,
                "--status",
                "enabled",
                "--no-headers",
                "--text",
                "--delimiter",
                ",",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search(firewall_id + "," + updated_label + ",enabled", result)


@pytest.mark.skip("skip until there is a way to delete default firewall")
def test_firewall_settings_update_and_list(test_firewall_id):
    for cmd in [
        BASE_CMD
        + [
            "firewall-settings-update",
            "--default_firewall_ids.vpc_interfac",
            test_firewall_id,
            "--default_firewall_ids.public_interface",
            test_firewall_id,
            "--default_firewall_ids.nodebalancer",
            test_firewall_id,
            "--default_firewall_ids.linode",
            test_firewall_id,
            "--json",
        ],
        BASE_CMD
        + [
            "firewall-settings-list",
            "--json",
        ],
    ]:
        data = json.loads(exec_test_command(cmd).stdout.decode().rstrip())
        firewall_ids = data[0]["default_firewall_ids"]
        for key in [
            "linode",
            "nodebalancer",
            "public_interface",
            "vpc_interface",
        ]:
            assert firewall_ids[key] == int(test_firewall_id)


def test_firewall_templates_list(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    data = json.loads(
        exec_test_command(BASE_CMD + ["templates-list", "--json"])
        .stdout.decode()
        .rstrip()
    )

    slugs = {template["slug"] for template in data}
    expected_slugs = {"akamai-non-prod", "vpc", "public"}
    assert expected_slugs.issubset(slugs)

    for template in data:
        assert "slug" in template
        assert "rules" in template
        rules = template["rules"]

        assert "inbound_policy" in rules
        assert "outbound_policy" in rules
        assert isinstance(rules.get("inbound", []), list)
        assert isinstance(rules.get("outbound", []), list)

        for rule in rules.get("inbound", []):
            assert "action" in rule
            assert "protocol" in rule
            assert "label" in rule
            assert "addresses" in rule


def test_firewall_template_view(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    for slug in ["akamai-non-prod", "vpc", "public"]:
        data = json.loads(
            exec_test_command(BASE_CMD + ["template-view", slug, "--json"])
            .stdout.decode()
            .rstrip()
        )
        template = data[0]

        assert template["slug"] == slug
        assert "rules" in template
        assert "inbound" in template["rules"]
        assert "outbound" in template["rules"]
        assert "inbound_policy" in template["rules"]
        assert "outbound_policy" in template["rules"]
        assert template["rules"]["inbound_policy"] == "DROP"
        assert template["rules"]["outbound_policy"] == "ACCEPT"
        assert isinstance(template["rules"]["inbound"], list)
        assert isinstance(template["rules"]["outbound"], list)
