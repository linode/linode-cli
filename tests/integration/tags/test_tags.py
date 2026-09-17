import json

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
)
from tests.integration.networking.fixtures import (  # noqa: F401
    create_reserved_ip,
)


@pytest.fixture(scope="session")
def create_tag_instance():
    unique_tag = get_random_text(5) + "-tag"

    exec_test_command(
        BASE_CMDS["tags"]
        + ["create", "--label", unique_tag, "--text", "--no-headers"]
    )

    yield unique_tag

    delete_target_id("tags", unique_tag)


@pytest.fixture
def create_tag_instance_for_reserved_ip(create_reserved_ip):
    res_ip_data = create_reserved_ip
    tag_label = get_random_text(5) + "-tag"

    exec_test_command(
        BASE_CMDS["tags"]
        + [
            "create",
            "--label",
            tag_label,
            "--reserved_ipv4_addresses",
            res_ip_data["address"],
        ]
    )

    yield res_ip_data, tag_label

    result = exec_test_command(
        BASE_CMDS["tags"] + ["list", "--text", "--no-headers"]
    )

    if tag_label in result:
        delete_target_id("tags", tag_label)


@pytest.mark.smoke
def test_view_unique_tag(create_tag_instance):
    result = exec_test_command(
        BASE_CMDS["tags"] + ["list", "--text", "--no-headers"]
    )
    assert create_tag_instance in result


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


def test_create_delete_tag_for_reserved_ip(create_tag_instance_for_reserved_ip):
    res_ip_data, tag_label = create_tag_instance_for_reserved_ip

    result = json.loads(
        exec_test_command(
            BASE_CMDS["tags"]
            + [
                "get-tagged-objects",
                tag_label,
                "--json",
            ]
        )
    )[0]
    headers = list(result.keys())

    assert_headers_in_lines(["data", "type"], [headers])
    assert result["data"]["address"] == res_ip_data["address"]
    assert result["data"]["reserved"] == True
    assert len(result["data"]["tags"]) == 1
    assert result["data"]["tags"][0] == tag_label
    assert result["type"] == "reserved_ipv4_address"

    exec_test_command(
        BASE_CMDS["tags"]
        + [
            "delete",
            tag_label,
        ]
    )

    result = exec_test_command(
        BASE_CMDS["tags"] + ["list", "--text", "--no-headers"]
    )
    assert tag_label not in result
