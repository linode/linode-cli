import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
)


@pytest.fixture(scope="session")
def test_tag_instance():
    unique_tag = get_random_text(5) + "-tag"

    exec_test_command(
        BASE_CMDS["tags"]
        + ["create", "--label", unique_tag, "--text", "--no-headers"]
    )

    yield unique_tag

    delete_target_id("tags", unique_tag)


@pytest.mark.smoke
def test_view_unique_tag(test_tag_instance):
    result = exec_test_command(
        BASE_CMDS["tags"] + ["list", "--text", "--no-headers"]
    )
    assert test_tag_instance in result


@pytest.mark.skip(reason="BUG = TPT-3650")
def test_fail_to_create_tag_shorter_than_three_char():
    bad_tag = "aa"
    result = exec_failing_test_command(
        BASE_CMDS["tags"]
        + ["create", "--label", bad_tag, "--text", "--no-headers"],
        ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 400" in result
    assert "Length must be 3-50 characters" in result
