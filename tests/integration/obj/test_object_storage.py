import json
from typing import Callable, Optional

import pytest
from pytest import MonkeyPatch

from tests.integration.helpers import exec_test_command, get_random_text
from tests.integration.obj.conftest import CLI_CMD, REGION, Keys


def test_clusters_list():
    response = (
        exec_test_command(CLI_CMD + ["clusters-list", "--json"])
        .stdout.decode()
        .rstrip()
    )

    clusters = json.loads(response)

    assert isinstance(clusters, list)
    assert len(clusters) > 0

    for cluster in clusters:
        assert isinstance(cluster, dict)
        assert {
            "id",
            "region",
            "status",
            "domain",
            "static_site_domain",
        }.issubset(cluster.keys())

        assert cluster["id"]
        assert cluster["region"]
        assert cluster["status"] in {"available", "unavailable"}
        assert cluster["domain"].endswith(".linodeobjects.com")
        assert cluster["static_site_domain"].startswith("website-")


def test_clusters_view():
    response = (
        exec_test_command(CLI_CMD + ["clusters-view", REGION, "--json"])
        .stdout.decode()
        .rstrip()
    )

    clusters = json.loads(response)

    assert isinstance(clusters, list)
    assert len(clusters) == 1

    for cluster in clusters:
        assert isinstance(cluster, dict)
        assert {
            "id",
            "region",
            "status",
            "domain",
            "static_site_domain",
        }.issubset(cluster.keys())

        assert cluster["id"] == "us-southeast-1"
        assert cluster["region"] == "us-southeast"
        assert cluster["status"] in {"available", "unavailable"}
        assert cluster["domain"].endswith(".linodeobjects.com")
        assert cluster["static_site_domain"].startswith("website-")


def test_keys_create(
    create_bucket: Callable[[Optional[str]], str],
    keys: Keys,
    monkeypatch: MonkeyPatch,
):
    bucket_name = create_bucket()
    region = "us-southeast"  # Fixed typo
    label = get_random_text(10)
    response = (
        exec_test_command(
            CLI_CMD
            + [
                "keys-create",
                "--label",
                label,
                "--bucket_access",
                f'[{{"region": "{region}", "bucket_name": "{bucket_name}", "permissions": "read_write"}}]',
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    data = json.loads(response)
    key = data[0]

    assert key["id"] > 0
    assert key["label"] == label
    assert key["access_key"]
    assert key["secret_key"]
    assert key["limited"] is True

    bucket = key["bucket_access"][0]
    assert bucket["cluster"] == "us-southeast-1"
    assert bucket["bucket_name"].startswith("test-bk")
    assert bucket["permissions"] == "read_write"
    assert bucket["region"] == "us-southeast"

    region_info = key["regions"][0]
    assert region_info["id"] == "us-southeast"
    assert region_info["s3_endpoint"].endswith(".linodeobjects.com")
    assert region_info["endpoint_type"] == "E0"

    exec_test_command(CLI_CMD + ["keys-delete", str(key["id"])])


def test_keys_delete():
    label = get_random_text(10)

    key = (
        exec_test_command(
            CLI_CMD
            + [
                "keys-create",
                "--label",
                label,
                "--text",
                "--no-headers",
                "--format=id",
            ]
        )
        .stdout.decode()
        .strip()
    )

    assert key, "Key creation failed, received empty key ID"

    # Delete the key
    exec_test_command(CLI_CMD + ["keys-delete", key])

    # Verify deletion by listing keys
    keys_list = (
        exec_test_command(CLI_CMD + ["keys-list", "--text"])
        .stdout.decode()
        .strip()
    )

    assert key not in keys_list, f"Key {key} still exists after deletion!"


def test_keys_list(test_key):
    keys_list = (
        exec_test_command(CLI_CMD + ["keys-list", "--text"])
        .stdout.decode()
        .strip()
    )

    assert test_key in keys_list


def test_keys_update(test_key):
    update_label = get_random_text(10)

    updated_key_resp = (
        exec_test_command(
            CLI_CMD
            + [
                "keys-update",
                test_key,
                "--label",
                update_label,
                "--region",
                "us-east",
                "--json",
            ]
        )
        .stdout.decode()
        .strip()
    )

    assert update_label in updated_key_resp


def test_keys_view(test_key):
    view_resp = (
        exec_test_command(
            CLI_CMD
            + [
                "keys-view",
                test_key,
                "--json",
            ]
        )
        .stdout.decode()
        .strip()
    )

    data = json.loads(view_resp)

    key = data[0]

    assert key["id"] > 0
    assert isinstance(key["label"], str) and key["label"]
    assert key["access_key"]
    assert key["secret_key"] == "[REDACTED]"
    assert isinstance(key["limited"], bool)

    region = key["regions"][0]
    assert region["id"] == "us-east"
    assert region["s3_endpoint"].endswith(".linodeobjects.com")
    assert region["endpoint_type"] in {"E0", "E1", "E2", "E3"}


def test_types():
    data = (
        exec_test_command(
            CLI_CMD
            + [
                "types",
                "--json",
            ]
        )
        .stdout.decode()
        .strip()
    )

    types = json.loads(data)

    assert isinstance(types, list) and len(types) > 0

    for type in types:
        assert "id" in type and isinstance(type["id"], str) and type["id"]
        assert (
            "label" in type and isinstance(type["label"], str) and type["label"]
        )
        assert "price" in type and isinstance(type["price"], dict)
        assert "hourly" in type["price"] and isinstance(
            type["price"]["hourly"], (int, float)
        )
        assert "monthly" in type["price"] and (
            type["price"]["monthly"] is None
            or isinstance(type["price"]["monthly"], (int, float))
        )
        assert "transfer" in type and isinstance(type["transfer"], int)

        if "region_prices" in type:
            assert isinstance(type["region_prices"], list)
            for region_price in type["region_prices"]:
                assert (
                    "id" in region_price
                    and isinstance(region_price["id"], str)
                    and region_price["id"]
                )
                assert "hourly" in region_price and isinstance(
                    region_price["hourly"], (int, float)
                )
                assert "monthly" in region_price and (
                    region_price["monthly"] is None
                    or isinstance(region_price["monthly"], (int, float))
                )


# TODO:: Add these two commands once v4.197.1 is released


def test_endpoints():
    data = (
        exec_test_command(
            CLI_CMD
            + [
                "endpoints",
                "--json",
            ]
        )
        .stdout.decode()
        .strip()
    )

    endpoints = json.loads(data)

    assert isinstance(endpoints, list)
    assert all("region" in e for e in endpoints)
    assert all("endpoint_type" in e for e in endpoints)
    assert all("s3_endpoint" in e for e in endpoints)

    us_east = next(e for e in endpoints if e["region"] == "us-east")
    assert us_east["endpoint_type"] == "E0"
    assert us_east["s3_endpoint"] == "us-east-1.linodeobjects.com"


@pytest.mark.skipif(
    reason="Skipping until the command is fixed and aligned with techdocs example. Applicable for spec version after 4.197.1"
)
def test_transfers():
    data = (
        exec_test_command(
            CLI_CMD
            + [
                "transfers",
                "--json",
            ]
        )
        .stdout.decode()
        .strip()
    )

    transfers = json.loads(data)

    assert len(transfers) > 0
    assert "used" in transfers[0]
    assert isinstance(transfers[0]["used"], int)
