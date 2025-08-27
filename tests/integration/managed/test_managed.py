import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    delete_target_id,
    exec_test_command,
    get_random_text,
)


def get_contact_id():
    contact_id = exec_test_command(
        BASE_CMDS["managed"]
        + [
            "contacts-list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    first_id = contact_id[0]
    return first_id


def test_managed_contact_create():
    unique_name = "test-user-" + get_random_text(5)
    exec_test_command(
        BASE_CMDS["managed"]
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
    res = exec_test_command(
        BASE_CMDS["managed"] + ["contacts-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["name", "email", "group"]
    assert_headers_in_lines(headers, lines)


def test_managed_contact_view():
    contact_id = get_contact_id()
    res = exec_test_command(
        BASE_CMDS["managed"]
        + ["contact-view", contact_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["name", "email", "group"]
    assert_headers_in_lines(headers, lines)


def test_managed_contact_update():
    contact_id = get_contact_id()
    unique_name_1 = get_random_text(5) + "test"
    update_name = exec_test_command(
        BASE_CMDS["managed"]
        + [
            "contact-update",
            contact_id,
            "--name",
            unique_name_1,
            "--text",
            "--no-headers",
            "--format=name",
        ]
    )
    assert update_name == unique_name_1
    delete_target_id(
        target="managed", delete_command="contact-delete", id=contact_id
    )


def test_managed_credential_create():
    unique_name = get_random_text(5) + "test"
    label = "test-label-" + get_random_text(5)
    password = get_random_text()
    exec_test_command(
        BASE_CMDS["managed"]
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
    res = exec_test_command(
        BASE_CMDS["managed"] + ["credentials-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["label", "last_decrypted"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def get_credential_id():
    credential_id = exec_test_command(
        BASE_CMDS["managed"]
        + [
            "credentials-list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    first_id = credential_id[0]
    yield first_id


def test_managed_credentials_view(get_credential_id):
    credential_id = get_credential_id
    res = exec_test_command(
        BASE_CMDS["managed"]
        + ["credential-view", credential_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["label", "last_decrypted"]
    assert_headers_in_lines(headers, lines)


def test_managed_credentials_update(get_credential_id):
    credential_id = get_credential_id
    new_label = "test-label" + get_random_text(4)
    update_label = exec_test_command(
        BASE_CMDS["managed"]
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
    assert update_label == new_label
    delete_target_id(
        target="managed", delete_command="credential-revoke", id=credential_id
    )


def test_managed_credentials_sshkey_view():
    res = exec_test_command(
        BASE_CMDS["managed"]
        + ["credential-sshkey-view", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["ssh_key"]
    assert_headers_in_lines(headers, lines)


def test_managed_issues_list():
    res = exec_test_command(
        BASE_CMDS["managed"] + ["issues-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["created", "services"]
    assert_headers_in_lines(headers, lines)


def test_managed_linode_settings_list():
    res = exec_test_command(
        BASE_CMDS["managed"]
        + ["linode-settings-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["label", "group"]
    assert_headers_in_lines(headers, lines)


def test_managed_linode_service_list():
    res = exec_test_command(
        BASE_CMDS["managed"] + ["services-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["service_type", "consultation_group"]
    assert_headers_in_lines(headers, lines)
