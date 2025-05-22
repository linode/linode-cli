import json

import pytest
from pytest import MonkeyPatch

from tests.integration.helpers import (
    delete_target_id,
    exec_test_command,
    get_random_text,
)
from tests.integration.linodes.helpers_linodes import (
    DEFAULT_LABEL,
    create_linode,
    wait_until,
)

linode_label = DEFAULT_LABEL + get_random_text(5)


@pytest.fixture(scope="session")
def linode_interface_public(linode_cloud_firewall):
    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        test_region="us-sea",
        interface_generation="linode",
        interfaces='[{"public": {"ipv4": {"addresses": [{"primary": true}]}}, "default_route": {"ipv4": true, "ipv6": true }, "firewall_id":'
        + linode_cloud_firewall
        + "}]",
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="session")
def linode_interface_vlan(linode_cloud_firewall):
    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        test_region="us-sea",
        interface_generation="linode",
        interfaces='[{"vlan": {"ipam_address": "10.0.0.1/24","vlan_label": "my-vlan"}}]',
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="session")
def linode_interface_legacy(linode_cloud_firewall):
    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        test_region="us-sea",
        interface_generation="legacy_config",
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="session")
def linode_interface_vpc(linode_cloud_firewall):
    vpc_output = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "vpcs",
                "create",
                "--label",
                get_random_text(5) + "-vpc",
                "--region",
                "us-sea",
                "--subnets.ipv4",
                "10.0.0.0/24",
                "--subnets.label",
                get_random_text(5) + "-vpc",
                "--json",
                "--suppress-warnings",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    subnet_id = vpc_output[0]["subnets"][0]["id"]

    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        test_region="us-sea",
        interface_generation="linode",
        interfaces='[{"default_route":{"ipv4":true},"firewall_id":'
        + str(linode_cloud_firewall)
        + ',"vpc":{"ipv4":{"addresses":[{"address":"auto","nat_1_1_address":"auto","primary":true}]},"subnet_id":'
        + str(subnet_id)
        + "}}]",
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)
    delete_target_id(target="vpcs", id=str(vpc_output[0]["id"]))


def get_interface_id(linode_id: str):
    data = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "interfaces-list",
                linode_id,
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    interface_id = data[0]["interfaces"]["id"]

    return str(interface_id)


def get_ipv4_addr(linode_id: "str"):
    data = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "ips-list",
                linode_id,
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    ipv4_public = data[0]["ipv4"]["public"]
    ipv4_addr = ipv4_public[0]["address"] if ipv4_public else None

    return str(ipv4_addr)


def test_interface_add(linode_cloud_firewall, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        test_region="us-sea",
        interface_generation="linode",
        interfaces='[{"public": {"ipv4": {"addresses": [{"primary": true}]}}, "default_route": {"ipv4": true, "ipv6": true }, "firewall_id":'
        + linode_cloud_firewall
        + "}]",
    )

    # wait until linode is running, wait_until returns True when it is in running state
    wait_until(linode_id=linode_id, timeout=240, status="running")

    interface_id = get_interface_id(linode_id)

    # shutdown linode and delete interface here to add new interface
    exec_test_command(["linode-cli", "linodes", "shutdown", linode_id])
    exec_test_command(
        ["linode-cli", "linodes", "interface-delete", linode_id, interface_id]
    )

    ip4_addr = get_ipv4_addr(linode_id)

    data = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "interface-add",
                linode_id,
                "--firewall_id",
                linode_cloud_firewall,
                "--default_route.ipv4",
                "true",
                "--public.ipv4.addresses",
                '[{"address": "'
                + ip4_addr
                + '", "primary": true}, {"address": "auto", "primary": false}]',
                "--public.ipv6.ranges",
                '[{"range": "/64"}, {"range": "/64"}]',
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    interface = data[0]

    assert "id" in interface
    assert "mac_address" in interface
    assert "default_route" in interface
    assert interface["default_route"].get("ipv4") is True

    ipv4 = interface.get("public", {}).get("ipv4", {})
    ipv4_addresses = ipv4.get("addresses", [])
    assert len(ipv4_addresses) == 2
    assert any(addr["primary"] for addr in ipv4_addresses)
    assert any(addr["address"] == ip4_addr for addr in ipv4_addresses)

    ipv6 = interface.get("public", {}).get("ipv6", {})
    ipv6_ranges = ipv6.get("ranges", [])
    assert len(ipv6_ranges) == 2
    assert all("range" in r for r in ipv6_ranges)

    slaac = ipv6.get("slaac", [])
    assert len(slaac) > 0

    delete_target_id(target="linodes", id=linode_id)


def test_interface_firewalls_list(linode_interface_public, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    linode_id = linode_interface_public
    interface_id = get_interface_id(linode_id)

    data = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "interface-firewalls-list",
                linode_id,
                interface_id,
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    firewall = data[0]

    assert "id" in firewall
    assert "label" in firewall and firewall["label"].startswith(
        "cloud_firewall"
    )
    assert "status" in firewall and firewall["status"] in [
        "enabled",
        "disabled",
    ]
    assert "rules" in firewall and isinstance(firewall["rules"], dict)


def test_interface_settings_update(linode_interface_public, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    linode_id = linode_interface_public
    interface_id = get_interface_id(linode_id)

    data = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "interface-settings-update",
                linode_id,
                "--network_helper",
                "true",
                "--default_route.ipv4_interface_id",
                interface_id,
                "--default_route.ipv6_interface_id",
                interface_id,
                "--default_route.ipv4_eligible_interface_ids",
                interface_id,
                "--default_route.ipv6_eligible_interface_ids",
                interface_id,
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    settings = data[0]
    assert settings["network_helper"] is True

    default_route = settings["default_route"]
    assert default_route["ipv4_interface_id"] == int(interface_id)
    assert default_route["ipv6_interface_id"] == int(interface_id)
    assert default_route["ipv4_eligible_interface_ids"] == [int(interface_id)]
    assert default_route["ipv6_eligible_interface_ids"] == [int(interface_id)]


def test_interface_update(linode_interface_public, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    linode_id = linode_interface_public
    interface_id = get_interface_id(linode_id)
    ipv4_addr = get_ipv4_addr(linode_id)

    # wait boot/provisioning
    wait_until(linode_id=linode_id, timeout=240, status="running")

    exec_test_command(["linode-cli", "linodes", "shutdown", linode_id])

    # wait shutdown
    wait_until(linode_id=linode_id, timeout=240, status="offline")

    data = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "interface-update",
                linode_id,
                interface_id,
                "--default_route.ipv4",
                "true",
                "--public.ipv4.addresses",
                '[{"address": "'
                + ipv4_addr
                + '", "primary": true}, {"address": "auto", "primary": false}]',
                "--public.ipv6.ranges",
                '[{"range": "/64"}, {"range": "/64"}]',
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert data[0]["id"] == int(interface_id)
    assert data[0]["default_route"]["ipv4"] is True

    ipv4_addresses = data[0]["public"]["ipv4"]["addresses"]
    assert any(
        addr["address"] == ipv4_addr and addr["primary"] is True
        for addr in ipv4_addresses
    )
    assert any(
        addr["address"] == "auto" or addr["primary"] is False
        for addr in ipv4_addresses
    )

    ipv6_ranges = data[0]["public"]["ipv6"]["ranges"]
    assert len(ipv6_ranges) == 2
    assert all("range" in r and r["range"].endswith("/64") for r in ipv6_ranges)


def test_interface_view(linode_interface_vpc, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    linode_id = linode_interface_vpc
    interface_id = get_interface_id(linode_id)

    data = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "interface-view",
                linode_id,
                interface_id,
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    interface = data[0]

    assert interface["id"] == int(interface_id)
    assert "mac_address" in interface
    assert "created" in interface
    assert "updated" in interface
    assert interface["default_route"]["ipv4"] is True

    assert "vpc" in interface
    assert "vpc_id" in interface["vpc"]
    assert "subnet_id" in interface["vpc"]
    assert "ipv4" in interface["vpc"]
    assert "addresses" in interface["vpc"]["ipv4"]
    assert any(
        addr["primary"] is True
        for addr in interface["vpc"]["ipv4"]["addresses"]
    )


def test_interfaces_list(linode_interface_vlan, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    linode_id = linode_interface_vlan

    data = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "interfaces-list",
                linode_id,
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert len(data) >= 1  # At least one interface listed

    for item in data:
        assert "interfaces" in item

        iface = item["interfaces"]

        assert "id" in iface
        assert isinstance(iface["id"], int)

        assert "mac_address" in iface
        assert isinstance(iface["mac_address"], str)

        assert "created" in iface
        assert "updated" in iface

        assert "default_route" in iface
        assert iface["default_route"]["ipv4"] is False
        assert iface["default_route"]["ipv6"] is False


@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_interfaces_upgrade(linode_interface_legacy, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")

    linode_id = linode_interface_legacy

    # wait boot/provisioning
    wait_until(linode_id=linode_id, timeout=240, status="running")

    exec_test_command(["linode-cli", "linodes", "shutdown", linode_id])

    # wait shutdown
    wait_until(linode_id=linode_id, timeout=240, status="offline")

    data = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "linodes",
                "interfaces-upgrade",
                linode_id,
                "--dry_run",
                "false",
                "--json",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    upgrade = data[0]
    assert "config_id" in upgrade
    assert upgrade["dry_run"] is False
    assert "interfaces" in upgrade
    assert isinstance(upgrade["interfaces"], list)
    assert len(upgrade["interfaces"]) > 0

    iface = upgrade["interfaces"][0]
    assert "id" in iface
    assert "mac_address" in iface
    assert "created" in iface
    assert "updated" in iface
    assert "default_route" in iface
    assert iface["default_route"].get("ipv4") is True

    assert "public" in iface
    ipv4 = iface["public"].get("ipv4", {})
    assert "addresses" in ipv4
    assert any(
        addr.get("primary") is True for addr in ipv4.get("addresses", [])
    )

    ipv6 = iface["public"].get("ipv6", {})
    assert "slaac" in ipv6
    assert isinstance(ipv6["slaac"], list)

    assert iface.get("vlan") is None
