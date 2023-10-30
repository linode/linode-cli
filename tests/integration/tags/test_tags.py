import time

import pytest

from tests.integration.helpers import (
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "tags"]
unique_tag = str(int(time.time())) + "-tag"


def test_display_tags():
    exec_test_command(BASE_CMD + ["list"])


@pytest.fixture(scope="session")
def test_tag_instance():
    exec_test_command(
        BASE_CMD + ["create", "--label", unique_tag, "--text", "--no-headers"]
    ).stdout.decode()

    yield unique_tag

    delete_target_id("tags", unique_tag)


@pytest.mark.smoke
def test_view_unique_tag(test_tag_instance):
    result = exec_test_command(
        BASE_CMD + ["list", "--text", "--no-headers"]
    ).stdout.decode()
    assert test_tag_instance in result


def test_fail_to_create_tag_shorter_than_three_char():
    bad_tag = "aa"
    result = exec_failing_test_command(
        BASE_CMD + ["create", "--label", bad_tag, "--text", "--no-headers"]
    ).stderr.decode()
    assert "Request failed: 400" in result
    assert "Length must be 3-50 characters" in result