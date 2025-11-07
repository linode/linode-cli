import jwt
import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command, get_random_text,
)


@pytest.fixture
def get_region():
    regions = exec_test_command(
        BASE_CMDS["regions"] + ["list", "--text", "--no-headers", "--delimiter", ",", "--format", "id"]
    ).splitlines()
    first_id = regions[0]
    yield first_id


@pytest.fixture(scope="function")
def create_image_id(get_region):
    linode_id = exec_test_command(
        BASE_CMDS["linodes"] + ["create", "--image", "linode/alpine3.22", "--region", get_region, "--type",
                                "g6-nanode-1", "--root_pass", "aComplex@Password", "--text", "--no-headers",
                                "--delimiter", ",", "--format", "id"]
    )
    disks = exec_test_command(
        BASE_CMDS["linodes"] + ["disks-list", linode_id, "--text", "--no-headers", "--delimiter", ",", "--format", "id"]
    ).splitlines()
    image_id = exec_test_command(
        BASE_CMDS["images"] + ["create", "--label", "linode-cli-test-image-sharing-image", "--disk_id", disks[0],
                               "--text", "--no-headers", "--delimiter", ",", "--format", "id"]
    )
    # TODO: wait_for_status
    yield linode_id, image_id


@pytest.fixture(scope="function")
def create_share_group():
    label = get_random_text(8) + "_sharegroup_cli_test"
    share_group = exec_test_command(
        BASE_CMDS["image-sharegroups"] + ["create", "--label", label, "--text", "--no-headers", "--delimiter", ",",
                                          "--format", "id,uuid"]
    ).split(",")
    yield share_group[0], share_group[1]


@pytest.fixture(scope="function")
def create_token():
    label = get_random_text(8) + "_sharegroup_cli_test"
    created_token = exec_test_command(
        BASE_CMDS["profile"] + ["token-create", "--label", label, "--text", "--no-headers", "--delimiter", ",",
                                "--format", "token"]
    )
    yield jwt.encode({"some": "payload"}, created_token, algorithm="HS256")
