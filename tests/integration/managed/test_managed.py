import secrets
import time

import pytest

from tests.integration.helpers import (
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
    get_random_text,
)

BASE_CMD = ["linode-cli", "managed"]
unique_name = "test-user-" + str(int(time.time()))


def test_managed_contact_create():
    exec_test_command(
        BASE_CMD
        + [
            "contact-create",
            "--name",
            unique_name,
            "--email",
            unique_name + "@linode.com",
            "--text",
            "--no-headers",
        ]
    )


def test_managed_contact_list():
    res = (
        exec_test_command(
            BASE_CMD + ["contacts-list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["name", "email", "group"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def test_contact_id():
    contact_id = (
        exec_test_command(
            BASE_CMD
            + [
                "contacts-list",
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
    first_id = contact_id[0]
    yield first_id


def test_managed_contact_view(test_contact_id):
    contact_id = test_contact_id
    res = (
        exec_test_command(
            BASE_CMD + ["contact-view", contact_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["name", "email", "group"]
    assert_headers_in_lines(headers, lines)


def test_managed_contact_update(test_contact_id):
    contact_id = test_contact_id
    unique_name1 = str(time.time_ns()) + "test"
    update_name = (
        exec_test_command(
            BASE_CMD
            + [
                "contact-update",
                contact_id,
                "--name",
                unique_name1,
                "--text",
                "--no-headers",
                "--format=name",
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    assert update_name == unique_name1
    delete_target_id(
        target="managed", subcommand="contact-delete", id=contact_id
    )


def test_managed_credential_create():
    label = "test-label" + secrets.token_hex(4)
    password = get_random_text()
    exec_test_command(
        BASE_CMD
        + [
            "credential-create",
            "--label",
            label,
            "--username",
            unique_name,
            "--password",
            password,
            "--text",
            "--no-headers",
        ]
    )


def test_managed_credentials_list():
    res = (
        exec_test_command(
            BASE_CMD + ["credentials-list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    credential_id = lines[1].split(",")[0]
    headers = ["label", "last_decrypted"]
    assert_headers_in_lines(headers, lines)
    return credential_id


@pytest.fixture
def test_credential_id():
    credential_id = (
        exec_test_command(
            BASE_CMD
            + [
                "credentials-list",
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
    first_id = credential_id[0]
    yield first_id


def test_managed_credentials_view(test_credential_id):
    credential_id = test_credential_id
    res = (
        exec_test_command(
            BASE_CMD
            + ["credential-view", credential_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["label", "last_decrypted"]
    assert_headers_in_lines(headers, lines)


def test_managed_credentials_update(test_credential_id):
    credential_id = test_credential_id
    new_label = "test-label" + secrets.token_hex(4)
    update_label = (
        exec_test_command(
            BASE_CMD
            + [
                "credential-update",
                credential_id,
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
    assert update_label == new_label
    delete_target_id(
        target="managed", subcommand="credential-revoke", id=credential_id
    )


def test_managed_credentials_sshkey_view():
    res = (
        exec_test_command(
            BASE_CMD + ["credential-sshkey-view", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["ssh_key"]
    assert_headers_in_lines(headers, lines)


def test_managed_issues_list():
    res = (
        exec_test_command(BASE_CMD + ["issues-list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["created", "services"]
    assert_headers_in_lines(headers, lines)


def test_managed_linode_settings_list():
    res = (
        exec_test_command(
            BASE_CMD + ["linode-settings-list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["label", "group"]
    assert_headers_in_lines(headers, lines)


def test_managed_linode_service_list():
    res = (
        exec_test_command(
            BASE_CMD + ["services-list", "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["service_type", "consultation_group"]
    assert_headers_in_lines(headers, lines)
