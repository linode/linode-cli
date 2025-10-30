import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
)


@pytest.fixture(scope="function")
def create_image():
    image_id = exec_test_command(
        BASE_CMDS["images"] + ["create", "--label", "testLabel", "--description", "Test description", "--disk_id"]
    )

    yield image_id

    delete_target_id(target="images", id=image_id)


@pytest.fixture(scope="function")
def create_share_group():
    image_id = exec_test_command(
        BASE_CMDS["images"] + ["create", "--label", "testLabel", "--description", "Test description", "--disk_id"]
    )

    share_group_id = exec_test_command(
        BASE_CMDS["images"]
        + ["sharegroups", "create", "--label", "my_label", "--description", "my_description", "--images",
           f'[{{"id": {image_id}, "label": "Linux Debian", "description": "Official Debian Linux image '
           'for server deployment"}]', "--delimiter", ",", "--text", "--no-headers"]
    )

    yield share_group_id, "uid"

    delete_target_id(target="images", id=image_id)


@pytest.fixture(scope="function")
def create_token():
    token_id = exec_test_command(
        BASE_CMDS["images"] + ["create", "--label", "testLabel", "--description", "Test description", "--disk_id"]
    )

    yield token_id

    delete_target_id(target="images", id=token_id)
