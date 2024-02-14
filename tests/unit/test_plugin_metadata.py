import importlib

import pytest
from linode_metadata.objects.instance import InstanceResponse
from linode_metadata.objects.networking import NetworkResponse
from linode_metadata.objects.ssh_keys import SSHKeysResponse
from pytest import CaptureFixture

from linodecli.plugins.metadata import (
    print_instance_table,
    print_networking_tables,
    print_ssh_keys_table,
)

plugin = importlib.import_module("linodecli.plugins.metadata")

INSTANCE = InstanceResponse(
    json_data={
        "id": 1,
        "host_uuid": "test_uuid",
        "label": "test-label",
        "region": "us-southeast",
        "tags": "test-tag",
        "type": "g6-standard-1",
        "specs": {"vcpus": 2, "disk": 3, "memory": 4, "transfer": 5, "gpus": 6},
        "backups": {"enabled": False, "status": ["test1", "test2"]},
    }
)

NETWORKING = NetworkResponse(
    json_data={
        "interfaces": [
            {
                "label": "interface-label-1",
                "purpose": "purpose-1",
                "ipam_address": ["address1", "address2"],
            },
            {
                "label": "interface-label-2",
                "purpose": "purpose-2",
                "ipam_address": ["address3", "address4"],
            },
        ],
        "ipv4": {
            "public": ["public-1", "public-2"],
            "private": ["private-1", "private-2"],
            "shared": ["shared-1", "shared-2"],
        },
        "ipv6": {
            "slaac": "slaac-1",
            "link_local": "link-local-1",
            "ranges": ["range-1", "range-2"],
            "shared_ranges": ["shared-range-1", "shared-range-2"],
        },
    }
)

SSH_KEYS = SSHKeysResponse(
    json_data={"users": {"root": ["ssh-key-1", "ssh-key-2"]}}
)

SSH_KEYS_EMPTY = SSHKeysResponse(json_data={"users": {"root": None}})


def test_print_help(capsys: CaptureFixture):
    with pytest.raises(SystemExit) as err:
        plugin.call(["--help"], None)

    captured_text = capsys.readouterr().out

    assert err.value.code == 0
    assert "Available endpoints: " in captured_text
    assert "Get information about public SSH Keys" in captured_text


def test_faulty_endpoint(capsys: CaptureFixture):
    with pytest.raises(SystemExit) as err:
        plugin.call(["blah"], None)

    captured_text = capsys.readouterr().out

    assert err.value.code == 0
    assert "Available endpoints: " in captured_text
    assert "Get information about public SSH Keys" in captured_text


def test_instance_table(capsys: CaptureFixture):
    # Note: Test is brief since table is very large with all values included and captured text abbreviates a lot of values
    print_instance_table(INSTANCE)
    captured_text = capsys.readouterr()

    assert "id" in captured_text.out
    assert "1" in captured_text.out

    assert "3" in captured_text.out
    assert "2" in captured_text.out


def test_networking_table(capsys: CaptureFixture):
    print_networking_tables(NETWORKING)
    captured_text = capsys.readouterr()

    assert "purpose" in captured_text.out
    assert "purpose-1" in captured_text.out

    assert "ip address" in captured_text.out
    assert "private-1" in captured_text.out
    assert "type" in captured_text.out
    assert "shared" in captured_text.out

    assert "slaac" in captured_text.out
    assert "slaac-1" in captured_text.out


def test_ssh_key_table(capsys: CaptureFixture):
    print_ssh_keys_table(SSH_KEYS)
    captured_text = capsys.readouterr()

    assert "user" in captured_text.out
    assert "ssh key" in captured_text.out
    assert "root" in captured_text.out
    assert "ssh-key-1" in captured_text.out
    assert "ssh-key-2" in captured_text.out


def test_empty_ssh_key_table(capsys: CaptureFixture):
    print_ssh_keys_table(SSH_KEYS_EMPTY)
    captured_text = capsys.readouterr()

    assert "user" in captured_text.out
    assert "ssh key" in captured_text.out
