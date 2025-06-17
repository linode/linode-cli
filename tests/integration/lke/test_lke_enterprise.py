import json
import re

from pytest import MonkeyPatch

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
)
from tests.integration.lke.helpers import get_cluster_id, get_lke_enterprise_id


def test_enterprise_tier_available_in_types(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    lke_types = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "types",
            "--text",
        ]
    )

    assert "lke-e" in lke_types
    assert "LKE Enterprise" in lke_types
    assert "price.monthly" in lke_types


def test_create_lke_enterprise(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    label = get_random_text(8)
    test_region = get_random_region_with_caps(
        required_capabilities=["Linodes", "Kubernetes Enterprise"]
    )

    k8s_version = get_lke_enterprise_id()

    output = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "cluster-create",
            "--label",
            label,
            "--tier",
            "enterprise",
            "--k8s_version",
            k8s_version,
            "--node_pools.type",
            "g6-standard-6",
            "--node_pools.count",
            "3",
            "--region",
            test_region,
            "--text",
        ]
    )

    headers = [
        "id",
        "label",
        "region",
        "k8s_version",
        "control_plane.high_availability",
        "tier",
    ]

    assert_headers_in_lines(headers, output.splitlines())

    assert label in output
    assert k8s_version in output
    assert "enterprise" in output

    delete_target_id(
        target="lke",
        id=get_cluster_id(label=label),
        delete_command="cluster-delete",
    )


def test_lke_tiered_versions_list():
    enterprise_tier_info_list = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "tiered-versions-list",
            "enterprise",
            "--json",
        ]
    )

    parsed = json.loads(enterprise_tier_info_list)

    enterprise_ti = parsed[0]

    assert re.match(r"^v\d+\.\d+\.\d+\+lke\d+$", enterprise_ti.get("id"))
    assert enterprise_ti.get("tier") == "enterprise"

    standard_tier_info_list = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "tiered-versions-list",
            "standard",
            "--json",
        ]
    )

    s_ti_list = json.loads(standard_tier_info_list)
    version_pattern = r"^\d+\.\d+$"

    for item in s_ti_list:
        assert re.match(version_pattern, item.get("id"))
        assert item.get("tier") == "standard"


def test_lke_tiered_versions_view():
    enterprise_id = get_lke_enterprise_id()
    enterprise_tier_info = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "tiered-version-view",
            "enterprise",
            enterprise_id,
            "--json",
        ]
    )

    parsed = json.loads(enterprise_tier_info)

    enterprise_ti = parsed[0]

    assert enterprise_ti.get("id") == enterprise_id
    assert enterprise_ti.get("tier") == "enterprise"

    standard_tier_info = exec_test_command(
        BASE_CMDS["lke"]
        + [
            "tiered-version-view",
            "standard",
            "1.31",
            "--json",
        ]
    )

    parsed = json.loads(standard_tier_info)

    stardard_ti = parsed[0]

    assert stardard_ti.get("tier") == "standard"
