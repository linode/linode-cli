import json

from pytest import MonkeyPatch

from tests.integration.helpers import (
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
    get_cluster_id,
    get_random_region_with_caps,
    get_random_text,
)

BASE_CMD = ["linode-cli", "lke"]


def test_enterprise_tier_available_in_types(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    lke_types = (
        exec_test_command(
            BASE_CMD
            + [
                "types",
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
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

    output = (
        exec_test_command(
            BASE_CMD
            + [
                "cluster-create",
                "--label",
                label,
                "--tier",
                "enterprise",
                "--k8s_version",
                "v1.31.1+lke4",
                "--node_pools.type",
                "g6-standard-6",
                "--node_pools.count",
                "3",
                "--region",
                test_region,
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
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
    assert "v1.31.1+lke4" in output
    assert "enterprise" in output

    delete_target_id(
        target="lke",
        id=get_cluster_id(label=label),
        delete_command="cluster-delete",
    )


def test_lke_tiered_versions_list():
    enterprise_tier_info_list = (
        exec_test_command(
            BASE_CMD
            + [
                "tiered-versions-list",
                "enterprise",
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    parsed = json.loads(enterprise_tier_info_list)

    enterprise_ti = parsed[0]

    assert enterprise_ti.get("id") == "v1.31.1+lke4"
    assert enterprise_ti.get("tier") == "enterprise"

    standard_tier_info_list = (
        exec_test_command(
            BASE_CMD
            + [
                "tiered-versions-list",
                "standard",
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    s_ti_list = json.loads(standard_tier_info_list)

    assert s_ti_list[0].get("id") == "1.32"
    assert s_ti_list[0].get("tier") == "standard"
    assert s_ti_list[1].get("id") == "1.31"
    assert s_ti_list[1].get("tier") == "standard"


def test_lke_tiered_versions_view():
    enterprise_tier_info = (
        exec_test_command(
            BASE_CMD
            + [
                "tiered-version-view",
                "enterprise",
                "v1.31.1+lke4",
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    parsed = json.loads(enterprise_tier_info)

    enterprise_ti = parsed[0]

    assert enterprise_ti.get("id") == "v1.31.1+lke4"
    assert enterprise_ti.get("tier") == "enterprise"

    standard_tier_info = (
        exec_test_command(
            BASE_CMD
            + [
                "tiered-version-view",
                "standard",
                "1.31",
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    parsed = json.loads(standard_tier_info)

    stardard_ti = parsed[0]

    assert stardard_ti.get("id") == "1.31"
    assert stardard_ti.get("tier") == "standard"
