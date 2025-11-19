from pytest import MonkeyPatch

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    assert_help_actions_list,
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
)
from tests.integration.sharegroups.fixtures import (  # noqa: F401
    create_image_id,
    create_share_group,
    get_region,
)


def test_help_image_sharegroups(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    output = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["--help", "--text", "--delimiter=,"]
    )
    actions = [
        "create",
        "delete, rm",
        "image-add",
        "image-remove",
        "image-update",
        "images-list",
        "images-list-by-token",
        "list, ls",
        "member-add",
        "member-delete",
        "member-update",
        "member-view",
        "members-list",
        "token-create",
        "token-delete",
        "token-update",
        "token-view",
        "tokens-list",
        "update",
        "view",
        "view-by-token",
    ]
    assert_help_actions_list(actions, output)


def test_list_all_share_groups(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["list", "--delimiter", ",", "--text"]
    )
    lines = result.splitlines()
    headers = [
        "id",
        "label",
        "uuid",
        "description",
        "is_suspended",
        "images_count",
        "members_count",
    ]
    assert_headers_in_lines(headers, lines)


def test_add_list_update_remove_image_to_share_group(
    create_share_group, create_image_id, monkeypatch: MonkeyPatch
):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result_add_image = exec_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "image-add",
            "--images.id",
            create_image_id[1],
            create_share_group[0],
            "--delimiter",
            ",",
            "--text",
        ]
    ).splitlines()
    headers = [
        "id",
        "label",
        "description",
        "size",
        "total_size",
        "capabilities",
        "is_public",
        "is_shared",
        "tags",
    ]
    assert_headers_in_lines(headers, result_add_image)
    assert "linode-cli-test-image-sharing-image" in result_add_image[1]

    result_list = exec_test_command(
        BASE_CMDS["image-sharegroups"]
        + ["images-list", create_share_group[0], "--delimiter", ",", "--text"]
    ).splitlines()
    headers = [
        "id",
        "label",
        "description",
        "size",
        "total_size",
        "capabilities",
        "is_public",
        "is_shared",
        "tags",
    ]
    assert_headers_in_lines(headers, result_list)
    assert "linode-cli-test-image-sharing-image" in result_list[1]
    share_image_id = result_list[1].split(",")[0]

    result_update_image = exec_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "image-update",
            create_share_group[0],
            share_image_id,
            "--label",
            "updated_label",
            "--description",
            "Updated description.",
            "--delimiter",
            ",",
            "--text",
        ]
    ).splitlines()
    assert_headers_in_lines(headers, result_update_image)
    assert "updated_label" in result_update_image[1]
    assert "Updated description." in result_update_image[1]

    exec_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "image-remove",
            create_share_group[0],
            share_image_id,
            "--delimiter",
            ",",
            "--text",
        ]
    ).splitlines()

    result_list = exec_test_command(
        BASE_CMDS["image-sharegroups"]
        + ["images-list", create_share_group[0], "--delimiter", ",", "--text"]
    )
    assert "linode-cli-test-image-sharing-image" not in result_list
    assert "updated_label" not in result_list

    delete_target_id(target="image-sharegroups", id=create_share_group[0])
    delete_target_id(target="images", id=create_image_id[1])
    delete_target_id(target="linodes", id=create_image_id[0])


def test_try_add_member_use_invalid_token(
    create_share_group, monkeypatch: MonkeyPatch
):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result = exec_failing_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "member-add",
            "--token",
            "notExistingToken",
            "--label",
            "test add member",
            create_share_group[0],
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 500" in result
    assert "Invalid token format" in result

    delete_target_id(target="image-sharegroups", id=create_share_group[0])


def test_list_members_for_invalid_token(
    create_share_group, monkeypatch: MonkeyPatch
):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result = exec_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "members-list",
            "--token",
            "notExistingToken",
            create_share_group[0],
            "--delimiter",
            ",",
            "--text",
        ]
    ).splitlines()
    headers = ["token_uuid", "label", "status"]
    assert_headers_in_lines(headers, result)

    delete_target_id(target="image-sharegroups", id=create_share_group[0])


def test_try_revoke_membership_for_invalid_token(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result = exec_failing_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "member-delete",
            "9876543",
            "notExistingToken",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Not found" in result


def test_try_update_membership_for_invalid_token(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result = exec_failing_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "member-update",
            "9876543",
            "notExistingToken",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
            "--label",
            "update",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Not found" in result


def test_try_view_membership_for_invalid_token(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result = exec_failing_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "member-view",
            "9876543",
            "notExistingToken",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Not found" in result


def test_create_read_update_delete_share_group(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    group_label = get_random_text(8) + "_sharegroup_cli_test"
    create_result = exec_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "create",
            "--label",
            group_label,
            "--description",
            "Test create",
            "--delimiter",
            ",",
            "--text",
        ]
    ).splitlines()
    headers = [
        "id",
        "label",
        "uuid",
        "description",
        "is_suspended",
        "images_count",
        "members_count",
    ]
    assert_headers_in_lines(headers, create_result)
    assert group_label in create_result[1]
    assert "Test create" in create_result[1]
    share_group_id = create_result[1].split(",")[0]

    get_result = exec_test_command(
        BASE_CMDS["image-sharegroups"]
        + ["view", share_group_id, "--delimiter", ",", "--text"]
    ).splitlines()
    assert_headers_in_lines(headers, get_result)
    assert group_label in get_result[1]

    update_result = exec_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "update",
            "--description",
            "Description update",
            "--label",
            group_label + "_updated",
            share_group_id,
            "--delimiter",
            ",",
            "--text",
        ]
    ).splitlines()
    assert_headers_in_lines(headers, update_result)
    assert group_label + "_updated" in update_result[1]
    assert "Description update" in update_result[1]

    exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["delete", share_group_id]
    )
    result_after_delete = exec_failing_test_command(
        BASE_CMDS["image-sharegroups"]
        + ["view", share_group_id, "--delimiter", ",", "--text"],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result_after_delete
    assert "Not found" in result_after_delete


def test_try_to_create_token(create_share_group, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    share_group_uuid = create_share_group[1]
    result = exec_failing_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "token-create",
            "--label",
            "cli_test",
            "--valid_for_sharegroup_uuid",
            share_group_uuid,
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 400" in result
    assert "You may not create a token for your own sharegroup" in result

    delete_target_id(target="image-sharegroups", id=create_share_group[0])


def test_try_read_invalid_token(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result = exec_failing_test_command(
        BASE_CMDS["image-sharegroups"]
        + ["token-view", "36b0-4d52_invalid", "--delimiter", ",", "--text"],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Not found" in result


def test_try_to_update_invalid_token(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result = exec_failing_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "token-update",
            "--label",
            "cli_test_update",
            "36b0-4d52_invalid",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Not found" in result


def test_try_to_delete_token(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result = exec_failing_test_command(
        BASE_CMDS["image-sharegroups"]
        + ["token-delete", "36b0-4d52_invalid", "--delimiter", ",", "--text"],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Not found" in result


def test_get_details_about_all_the_users_tokens(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result = exec_test_command(
        BASE_CMDS["image-sharegroups"]
        + ["tokens-list", "--delimiter", ",", "--text"]
    )
    lines = result.splitlines()
    headers = [
        "token_uuid",
        "label",
        "status",
        "valid_for_sharegroup_uuid",
        "sharegroup_uuid",
        "sharegroup_label",
    ]
    assert_headers_in_lines(headers, lines)


def test_try_to_list_all_shared_images_for_invalid_token(
    monkeypatch: MonkeyPatch,
):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result = exec_failing_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "images-list-by-token",
            "notExistingToken",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Not found" in result


def test_try_gets_details_about_your_share_group_for_invalid_token(
    monkeypatch: MonkeyPatch,
):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    result = exec_failing_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "view-by-token",
            "notExistingToken",
            "--delimiter",
            ",",
            "--text",
            "--no-headers",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Not found" in result
