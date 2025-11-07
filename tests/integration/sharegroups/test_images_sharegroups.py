from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    assert_headers_in_lines,
    BASE_CMDS,
    delete_target_id,
    exec_test_command, get_random_text, exec_failing_test_command,
)
from tests.integration.sharegroups.fixtures import (
    create_image_id,
    create_share_group,
    get_region,
    create_token,
)

# def test_help_image_sharegroups():
#     output = exec_test_command(
#         BASE_CMDS["image-sharegroups"] + ["--help", "--text", "--delimiter=,"]
#     )
#     actions = [
#         "create",
#         "delete",
#         "image-add",
#         "image-remove",
#         "image-update",
#         "images-list",
#         "images-list-by-token",
#         "list, ls",
#         "member-add",
#         "member-delete",
#         "member-update",
#         "member-view",
#         "members-list",
#         "token-create",
#         "token-delete",
#         "token-update",
#         "token-view",
#         "tokens-list",
#         "update",
#         "view",
#         "view-by-token"
#     ]
#     assert_help_actions_list(actions, output)


def test_list_all_share_groups():
    result = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["list", "--delimiter", ",", "--text"]
    )
    lines = result.splitlines()
    headers = ["id", "label", "uuid", "description", "is_suspended", "images_count", "members_count"]
    assert_headers_in_lines(headers, lines)


def test_list_all_owned_groups_with_shared_images():
    result = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["list", "--delimiter", ",", "--text"]
    ).splitlines()
    headers = ["id", "label", "uuid", "description", "is_suspended", "images_count", "members_count"]
    assert_headers_in_lines(headers, result)


def test_add_image_to_share_group_list_images(create_share_group, create_image_id):
    result_add_image = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["image-add", "--images.id", create_image_id[1], create_share_group[0],
                                          "--delimiter", ",",  "--text"]
    ).splitlines()
    headers = ["id", "label", "description", "size", "total_size", "capabilities", "is_public", "is_shared", "tags"]
    assert_headers_in_lines(headers, result_add_image)
    assert "linode-cli-test-image-sharing-image" in result_add_image[1]

    result_list = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["images-list", create_share_group[0], "--delimiter", ",", "--text"]
    ).splitlines()
    headers = ["id", "label", "description", "size", "total_size", "capabilities", "is_public", "is_shared", "tags"]
    assert_headers_in_lines(headers, result_list)
    assert "linode-cli-test-image-sharing-image" in result_list[1]

    delete_target_id(target="image-sharegroups", id=create_share_group[0])
    delete_target_id(target="images", id=create_image_id[1])
    delete_target_id(target="linodes", id=create_image_id[0])


def test_add_and_list_share_group_member(create_token, create_share_group):
    result_add = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["member-add", "--token", create_token, "--label", "test add member",
                                          create_share_group[0], "--delimiter", ",", "--text"]
    ).splitlines()
    headers = ["id", "label", "uuid", "description", "is_suspended", "images_count", "members_count"]
    assert_headers_in_lines(headers, result_add)
    assert "token_uuid" in result_add[1]
    assert create_token in result_add[1]

    result_list = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["members-list", create_share_group[0], "members", "list", "--delimiter", ",",
                                          "--text"]
    ).splitlines()
    headers = ["id", "label", "uuid", "description", "is_suspended", "images_count", "members_count"]
    assert_headers_in_lines(headers, result_list)
    assert "token_uuid" in result_list[1]
    assert "Test create" in result_list[1]

    delete_target_id(target="profile", id=create_token)
    delete_target_id(target="image-sharegroups", id=create_share_group[0])


def test_create_read_update_delete_share_group():
    group_label = get_random_text(8) + "_sharegroup_cli_test"
    create_result = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["create", "--label", group_label, "--description", "Test create",
                                          "--delimiter", ",", "--text"]
    ).splitlines()
    headers = ["id", "label", "uuid", "description", "is_suspended", "images_count", "members_count"]
    assert_headers_in_lines(headers, create_result)
    assert group_label in create_result[1]
    assert "Test create" in create_result[1]
    share_group_id = create_result[1].split(",")[0]

    get_result = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["view", share_group_id, "--delimiter", ",", "--text"]
    ).splitlines()
    assert_headers_in_lines(headers, get_result)
    assert group_label in get_result[1]

    update_result = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["update", "--description", "Description update", "--label", group_label +
                                          "_updated", share_group_id, "--delimiter", ",", "--text"]
    ).splitlines()
    assert_headers_in_lines(headers, update_result)
    assert group_label + "_updated" in update_result[1]
    assert "Description update" in update_result[1]

    exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["delete", share_group_id]
    )
    result_after_delete = exec_failing_test_command(
        BASE_CMDS["image-sharegroups"] + ["view", share_group_id, "--delimiter", ",", "--text"],
        expected_code=ExitCodes.REQUEST_FAILED
    )
    assert "Request failed: 403" in result_after_delete


def test_create_token(create_share_group):
    share_group_uuid = create_share_group[1]
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", "create", "--label", "my_token", "--valid_for_sharegroup_uuid",
                               share_group_uuid, "--delimiter", ",", "--text"]
    )
    assert "token_uuid" in result


def test_get_details_about_all_the_users_tokens():
    result = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["tokens-list", "--delimiter", ",", "--text"]
    )
    lines = result.splitlines()
    headers = ["token_uuid", "label", "status", "valid_for_sharegroup_uuid", "sharegroup_uuid", "sharegroup_label"]
    assert_headers_in_lines(headers, lines)


def test_update_and_revoke_access_to_shared_image(create_image_id, create_share_group):
    image_id = create_image_id[0]
    share_group_id = create_share_group[0]
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "images", "update", image_id, "--label", "new_label",
                               "--description", "A new description.", "--delimiter", ",", "--text"]
    )
    assert "image_sharing" in result
    exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "images", "remove", image_id, "--delimiter", ",",
                               "--text"]
    )
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "images", "update", image_id, "--label", "new_label",
                               "--description", "A new description.", "--delimiter", ",", "--text"]
    )
    assert "Request failed: 400" in result


def test_get_and_revoke_membership_token_details(create_share_group, create_token):
    share_group_id = create_share_group[0]
    token_id = create_token[0]
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "members", "view", token_id, "--delimiter", ",", "--text",
                               "--no-headers"]
    )
    assert "token_uuid" in result
    token_id = create_token[0]
    exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "members", "delete", token_id, "--delimiter", ",",
                               "--text"]
    )
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "members", "view", token_id, "--delimiter", ",", "--text",
                               "--no-headers"]
    )
    assert "Request failed: 400" in result


def test_create_and_update_membership_token(create_image_id, create_share_group, create_token):
    image_id = create_image_id[0]
    share_group_id = create_share_group[0]
    token_id = create_token[0]
    result = exec_test_command(
        BASE_CMDS["images"] + [image_id, "sharegroups", share_group_id, "members", "update", token_id, "--label",
                               "new_label", "--delimiter", ",", "--text"]
    )
    assert "label" in result


def test_list_all_shared_images(create_token):
    token_id = create_token[0]
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", token_id, "sharegroup", "images", "list", "--delimiter", ",",
                               "--text"]
    )
    assert "data" in result
    assert "image_sharing" in result


def test_gets_details_about_your_share_group(create_token):
    token_id = create_token[0]
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", token_id, "sharegroup", "view", "--delimiter", ",", "--text",
                               "--no-headers"]
    )
    assert "sharegroup_uuid" in result


def test_get_update_remove_membership_for_token(create_token):
    token_id = create_token[0]
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", "view", token_id, "--delimiter", ",", "--text"]
    )
    assert "sharegroup_uuid" in result
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", "update", token_id, "--label", "new_label", "--delimiter", ",",
                               "--text"]
    )
    assert "label" in result
    exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", "delete", token_id, "--delimiter", ",", "--text",
                               "--no-headers"]
    )
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", "view", token_id, "--delimiter", ",", "--text"]
    )
    assert "Request failed: 400" in result
