import time

import pytest

from tests.integration.helpers import (
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "object-storage"]


def test_clusters_list():
    res = (
        exec_test_command(
            BASE_CMD + ["clusters-list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["domain", "status", "region"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def test_cluster_id():
    cluster_id = (
        exec_test_command(
            BASE_CMD
            + [
                "clusters-list",
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )
    first_id = cluster_id[0]
    yield first_id


def test_clusters_view(test_cluster_id):
    cluster_id = test_cluster_id
    res = (
        exec_test_command(
            BASE_CMD + ["clusters-view", cluster_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["domain", "status", "region"]
    assert_headers_in_lines(headers, lines)


def test_create_obj_storage_key():
    new_label = str(time.time_ns()) + "label"
    exec_test_command(
        BASE_CMD
        + [
            "keys-create",
            "--label",
            new_label,
            "--text",
            "--no-headers",
        ]
    )


def test_obj_storage_key_list():
    res = (
        exec_test_command(BASE_CMD + ["keys-list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["label", "access_key", "secret_key"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def test_key_id():
    key_id = (
        exec_test_command(
            BASE_CMD
            + [
                "keys-list",
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )
    first_id = key_id[0]
    yield first_id


def test_obj_storage_key_view(test_key_id):
    key_id = test_key_id
    res = (
        exec_test_command(
            BASE_CMD + ["keys-view", key_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["label", "access_key", "secret_key"]
    assert_headers_in_lines(headers, lines)


def test_obj_storage_key_update(test_key_id):
    key_id = test_key_id
    new_label = str(time.time_ns()) + "label"
    updated_label = (
        exec_test_command(
            BASE_CMD
            + [
                "keys-update",
                key_id,
                "--label",
                new_label,
                "--text",
                "--no-headers",
                "--format=label",
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    assert new_label == updated_label
    delete_target_id(
        target="object-storage", subcommand="keys-delete", id=key_id
    )
