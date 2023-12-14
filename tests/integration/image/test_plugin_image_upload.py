import json
import os
import re
import subprocess
import tempfile
from sys import platform
from typing import List

import pytest

from tests.integration.helpers import get_random_text

REGION = "us-iad"
BASE_CMD = ["linode-cli", "image-upload", "--region", REGION]

# A minimal gzipped image that will be accepted by the API
TEST_IMAGE_CONTENT = (
    b"\x1F\x8B\x08\x08\xBD\x5C\x91\x60\x00\x03\x74\x65\x73\x74\x2E\x69"
    b"\x6D\x67\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00"
)


@pytest.fixture(scope="session", autouse=True)
def fake_image_file():
    with tempfile.NamedTemporaryFile(delete=False) as fp:
        fp.write(TEST_IMAGE_CONTENT)
        file_path = fp.name

    yield file_path

    os.remove(file_path)


def exec_test_command(args: List[str]):
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
    )
    return process


def test_help():
    process = exec_test_command(BASE_CMD + ["--help"])
    output = process.stdout.decode()

    assert process.returncode == 0
    assert "The image file to upload" in output
    assert "The region to upload the image to" in output


def test_invalid_file(
    fake_image_file,
):
    file_path = fake_image_file + "_fake"
    process = exec_test_command(
        BASE_CMD + ["--label", "notimportant", file_path]
    )
    output = process.stdout.decode()

    assert process.returncode == 2
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
    process = exec_test_command(
        BASE_CMD + ["--label", label, "--description", description, file_path]
    )

    output = process.stdout.decode()

    assert process.returncode == 0

    # Assertions now using keywords due to some chars getting cut off from lack of terminal space
    assert re.search("[0-9][0-9]+.[0-9]%", output)
    assert re.search("test", output)

    # Get the new image from the API
    process = exec_test_command(
        ["linode-cli", "images", "ls", "--json", "--label", label]
    )
    assert process.returncode == 0

    image = json.loads(process.stdout.decode())

    assert image[0]["label"] == label

    # Delete the image
    process = exec_test_command(["linode-cli", "images", "rm", image[0]["id"]])
    assert process.returncode == 0


@pytest.mark.skipif(platform == "win32", reason="Test N/A on Windows")
def test_file_upload_cloud_init(
    fake_image_file,
):
    file_path = fake_image_file
    label = f"cli-test-{get_random_text()}"
    description = "test description"

    # Upload the test image
    process = exec_test_command(
        BASE_CMD + ["--label", label, "--description", description, "--cloud-init", file_path]
    )

    assert process.returncode == 0

    # Get the new image from the API
    process = exec_test_command(
        ["linode-cli", "images", "ls", "--json", "--label", label]
    )
    assert process.returncode == 0

    image = json.loads(process.stdout.decode())

    assert image[0]["label"] == label
    assert "cloud-init" in image[0]["capabilities"]

    # Delete the image
    process = exec_test_command(["linode-cli", "images", "rm", image[0]["id"]])
    assert process.returncode == 0
