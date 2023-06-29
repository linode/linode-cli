import re
import time

import pytest

from tests.integration.helpers import (
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
)
from tests.integration.linodes.helpers_linodes import (
    BASE_CMD,
    DEFAULT_LABEL,
    DEFAULT_RANDOM_PASS,
    DEFAULT_TEST_IMAGE,
    wait_until,
)

timestamp = str(int(time.time()))
linode_label = DEFAULT_LABEL + timestamp


@pytest.fixture(scope="package", autouse=True)
def setup_linodes():
    linode_id = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--type",
                "g6-standard-2",
                "--region",
                "us-east",
                "--image",
                DEFAULT_TEST_IMAGE,
                "--label",
                linode_label,
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--text",
                "--delimiter",
                ",",
                "--no-headers",
                "--format",
                "id",
                "--no-defaults",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


def test_update_linode_with_a_image():
    result = exec_test_command(BASE_CMD + ["update", "--help"]).stdout.decode()

    assert "--image" not in result


@pytest.mark.smoke
def test_create_linodes_with_a_label(create_linode_with_label):
    result = create_linode_with_label

    assert re.search(
        "^cli(.*),us-east,g6-standard-2," + DEFAULT_TEST_IMAGE, result
    )


@pytest.mark.smoke
def test_view_linode_configuration(setup_linodes):
    linode_id = setup_linodes
    result = exec_test_command(
        BASE_CMD
        + [
            "view",
            linode_id,
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format",
            "id,label,region,type,image",
            "--no-defaults",
        ]
    ).stdout.decode()

    assert re.search(
        linode_id
        + ","
        + linode_label
        + ",us-east,g6-standard-2,"
        + DEFAULT_TEST_IMAGE,
        result,
    )


def test_create_linode_with_min_required_props(create_linode_min_req):
    result = create_linode_min_req
    assert re.search("[0-9]+,us-east,g6-standard-2", result)


def test_create_linodes_fails_without_a_root_pass():
    result = exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--type",
            "g6-standard-2",
            "--region",
            "us-east",
            "--image",
            DEFAULT_TEST_IMAGE,
            "--text",
            "--no-headers",
        ]
    ).stderr.decode()
    assert "Request failed: 400" in result
    assert "root_pass	root_pass is required" in result


def test_create_linode_without_image_and_not_boot(create_linode_wo_image):
    linode_id = create_linode_wo_image

    wait_until(linode_id=linode_id, timeout=180, status="offline")

    result = exec_test_command(
        BASE_CMD
        + ["view", linode_id, "--format", "status", "--text", "--no-headers"]
    ).stdout.decode()

    assert "offline" in result


def test_list_linodes(setup_linodes):
    result = exec_test_command(
        BASE_CMD + ["list", "--format", "label", "--text", "--no-headers"]
    ).stdout.decode()
    assert linode_label in result


def test_add_tag_to_linode(setup_linodes):
    linode_id = setup_linodes
    unique_tag = "tag" + str(int(time.time()))

    result = exec_test_command(
        BASE_CMD
        + [
            "update",
            linode_id,
            "--tags",
            unique_tag,
            "--format",
            "tags",
            "--text",
            "--no-headers",
        ]
    ).stdout.decode()

    assert unique_tag in result
