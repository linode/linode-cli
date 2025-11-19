import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
    get_random_text,
)


@pytest.fixture
def get_region():
    regions = exec_test_command(
        BASE_CMDS["regions"]
        + [
            "list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    first_id = regions[0]
    yield first_id


def wait_for_image_status(id, expected_status, timeout=180, interval=5):
    import time

    current_status = exec_test_command(
        BASE_CMDS["images"]
        + [
            "view",
            id,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "status",
        ]
    ).splitlines()
    timer = 0
    while current_status[0] != expected_status and timer < timeout:
        time.sleep(interval)
        timer += interval
        current_status = exec_test_command(
            BASE_CMDS["images"]
            + [
                "view",
                id,
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
                "--format",
                "status",
            ]
        ).splitlines()
    if timer >= timeout:
        raise TimeoutError(
            f"Created image did not reach status '{expected_status}' within {timeout} seconds."
        )


@pytest.fixture(scope="function")
def create_image_id(get_region):
    linode_id = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "create",
            "--image",
            "linode/alpine3.22",
            "--region",
            get_region,
            "--type",
            "g6-nanode-1",
            "--root_pass",
            "aComplex@Password",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    )
    disks = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "disks-list",
            linode_id,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    image_id = exec_test_command(
        BASE_CMDS["images"]
        + [
            "create",
            "--label",
            "linode-cli-test-image-sharing-image",
            "--disk_id",
            disks[0],
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    )
    wait_for_image_status(image_id, "available")
    yield linode_id, image_id


@pytest.fixture(scope="function")
def create_share_group():
    label = get_random_text(8) + "_sharegroup_cli_test"
    share_group = exec_test_command(
        BASE_CMDS["image-sharegroups"]
        + [
            "create",
            "--label",
            label,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id,uuid",
        ]
    ).split(",")
    yield share_group[0], share_group[1]
