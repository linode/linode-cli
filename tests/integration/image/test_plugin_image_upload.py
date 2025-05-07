import json
import re
from sys import platform

import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
)
from tests.integration.image.fixtures import fake_image_file  # noqa: F401
from tests.integration.image.helpers import get_first_image_id

BASE_CMD = BASE_CMDS["image-upload"] + ["--region", "us-iad"]


def test_help():
    output = exec_test_command(BASE_CMD + ["--help"])

    assert "The image file to upload" in output
    assert "The region to upload the image to" in output


def test_invalid_file(
    fake_image_file,
):
    file_path = fake_image_file + "_fake"
    output = exec_failing_test_command(
        BASE_CMD + ["--label", "notimportant", file_path], expected_code=8
    )

    assert f"No file at {file_path}" in output


@pytest.mark.smoke
@pytest.mark.skipif(platform == "win32", reason="Test N/A on Windows")
def test_file_upload(
    fake_image_file,
):
    file_path = fake_image_file
    label = f"cli-test-{get_random_text()}"
    description = "test description"

    # Upload the test image
    output = exec_test_command(
        BASE_CMD + ["--label", label, "--description", description, file_path]
    )

    # Assertions now using keywords due to some chars getting cut off from lack of terminal space
    assert re.search("[0-9][0-9]+.[0-9]%", output)
    assert re.search("test", output)

    # Get the new image from the API
    output = exec_test_command(
        ["linode-cli", "images", "ls", "--json", "--label", label]
    )
    image = json.loads(output)

    assert image[0]["label"] == label

    # Delete the image
    exec_test_command(["linode-cli", "images", "rm", image[0]["id"]])


@pytest.mark.skipif(platform == "win32", reason="Test N/A on Windows")
def test_file_upload_cloud_init(
    fake_image_file,
):
    file_path = fake_image_file
    label = f"cli-test-{get_random_text()}"
    description = "test description"

    # Upload the test image
    exec_test_command(
        BASE_CMD
        + [
            "--label",
            label,
            "--description",
            description,
            "--cloud-init",
            file_path,
        ]
    )

    # Get the new image from the API
    output = exec_test_command(
        ["linode-cli", "images", "ls", "--json", "--label", label]
    )

    image = json.loads(output)

    assert image[0]["label"] == label
    assert "cloud-init" in image[0]["capabilities"]

    # Delete the image
    exec_test_command(["linode-cli", "images", "rm", image[0]["id"]])


def test_image_list():
    res = exec_test_command(
        ["linode-cli", "images", "list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["label", "description"]
    assert_headers_in_lines(headers, lines)


def test_image_view():
    image_id = get_first_image_id()
    res = exec_test_command(
        [
            "linode-cli",
            "images",
            "view",
            image_id,
            "--text",
            "--delimiter=,",
        ]
    )
    lines = res.splitlines()

    headers = ["label", "description"]
    assert_headers_in_lines(headers, lines)

    assert "regions" in lines
    assert image_id in str(lines)
