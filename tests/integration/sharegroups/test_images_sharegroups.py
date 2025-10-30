from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
)


def test_list_all_share_groups():
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "list", "--delimiter", ",", "--text", "--no-headers"]
    )
    assert "is_shared" in result
    assert "image_sharing" in result


def test_list_all_owned_groups_with_shared_images(create_image):
    image_id = create_image[0]
    result = exec_test_command(
        BASE_CMDS["images"] + [image_id, "sharegroups", "list", "--delimiter", ",", "--text", "--no-headers"]
    )
    assert "data" in result


def test_add_image_to_share_group_list_images(create_share_group):
    share_group_id = create_share_group[0]
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "images", "add", "--delimiter", ",", "--text",
                               "--no-headers"]
    )
    assert "sharegroup_id" in result
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "images", "list", "--delimiter", ",", "--text",
                               "--no-headers"]
    )
    assert "sharegroup_id" in result


def test_add_and_list_share_group_member(create_share_group):
    share_group_id = create_share_group[0]
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "members", "add", "--token", "abc123", "--label",
                               "my_sharegroup_member", "--delimiter", ",", "--text", "--no-headers"]
    )
    assert "token_uuid" in result
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "members", "list", "--delimiter", ",", "--text",
                               "--no-headers"]
    )
    assert "token_uuid" in result


def test_create_read_update_delete_share_group(create_share_group):
    share_group_id = create_share_group[0]
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "view", share_group_id, "--delimiter", ",", "--text", "--no-headers"]
    )
    assert "id" + share_group_id in result
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "update", share_group_id, "--label", "new_label", "--description",
                               "A new description.", "--delimiter", ",", "--text", "--no-headers"]
    )
    assert "label" in result
    exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "delete", share_group_id, "--delimiter", ",", "--text", "--no-headers"]
    )
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "view", share_group_id, "--delimiter", ",", "--text", "--no-headers"]
    )
    assert "Request failed: 400" in result


def test_create_token(create_share_group):
    share_group_uuid = create_share_group[1]
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", "create", "--label", "my_token", "--valid_for_sharegroup_uuid",
                               share_group_uuid, "--delimiter", ",", "--text", "--no-headers"]
    )
    assert "token_uuid" in result


def test_get_details_about_all_the_users_tokens():
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", "list", "--delimiter", ",", "--text", "--no-headers"]
    )
    assert "token_uuid" in result


def test_update_and_revoke_access_to_shared_image(create_image, create_share_group):
    image_id = create_image[0]
    share_group_id = create_share_group[0]
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "images", "update", image_id, "--label", "new_label",
                               "--description", "A new description.", "--delimiter", ",", "--text", "--no-headers"]
    )
    assert "image_sharing" in result
    exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "images", "remove", image_id, "--delimiter", ",",
                               "--text", "--no-headers"]
    )
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "images", "update", image_id, "--label", "new_label",
                               "--description", "A new description.", "--delimiter", ",", "--text", "--no-headers"]
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
                               "--text", "--no-headers"]
    )
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", share_group_id, "members", "view", token_id, "--delimiter", ",", "--text",
                               "--no-headers"]
    )
    assert "Request failed: 400" in result


def test_create_and_update_membership_token(create_image, create_share_group, create_token):
    image_id = create_image[0]
    share_group_id = create_share_group[0]
    token_id = create_token[0]
    result = exec_test_command(
        BASE_CMDS["images"] + [image_id, "sharegroups", share_group_id, "members", "update", token_id, "--label",
                               "new_label", "--delimiter", ",", "--text", "--no-headers"]
    )
    assert "label" in result


def test_list_all_shared_images(create_token):
    token_id = create_token[0]
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", token_id, "sharegroup", "images", "list", "--delimiter", ",",
                               "--text", "--no-headers"]
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
        BASE_CMDS["images"] + ["sharegroups", "tokens", "view", token_id, "--delimiter", ",", "--text", "--no-headers"]
    )
    assert "sharegroup_uuid" in result
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", "update", token_id, "--label", "new_label", "--delimiter", ",",
                               "--text", "--no-headers"]
    )
    assert "label" in result
    exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", "delete", token_id, "--delimiter", ",", "--text",
                               "--no-headers"]
    )
    result = exec_test_command(
        BASE_CMDS["images"] + ["sharegroups", "tokens", "view", token_id, "--delimiter", ",", "--text", "--no-headers"]
    )
    assert "Request failed: 400" in result
