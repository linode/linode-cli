import os
import re

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
)
from tests.integration.volumes.fixtures import volume_instance_id  # noqa: #401


def test_fail_to_create_volume_under_10gb():
    label = get_random_text(8)

    result = exec_failing_test_command(
        BASE_CMDS["volumes"]
        + [
            "create",
            "--label",
            label,
            "--region",
            "us-ord",
            "--size",
            "5",
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    )

    if "test" == os.environ.get(
        "TEST_ENVIRONMENT", None
    ) or "dev" == os.environ.get("TEST_ENVIRONMENT", None):
        assert "size	Must be 10-1024" in result
    else:
        assert "size	Must be 10-16384" in result


def test_fail_to_create_volume_without_region():
    label = get_random_text(8)

    result = exec_failing_test_command(
        BASE_CMDS["volumes"]
        + [
            "create",
            "--label",
            label,
            "--size",
            "10",
            "--text",
            "--no-headers",
            "--no-defaults",
        ],
        ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 400" in result
    assert "Must provide a region or a Linode ID" in result


def test_fail_to_create_volume_without_label():
    result = exec_failing_test_command(
        BASE_CMDS["volumes"]
        + [
            "create",
            "--region",
            "us-ord",
            "--size",
            "10",
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 400" in result
    assert "label	label is required" in result


def test_fail_to_create_volume_over_1024gb_in_size():
    label = get_random_text(8)

    result = exec_failing_test_command(
        BASE_CMDS["volumes"]
        + [
            "create",
            "--label",
            label,
            "--region",
            "us-ord",
            "--size",
            "19000",
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    )
    if "test" == os.environ.get(
        "TEST_ENVIRONMENT", None
    ) or "dev" == os.environ.get("TEST_ENVIRONMENT", None):
        assert "size	Must be 10-1024" in result
    else:
        assert "size	Must be 10-16384" in result


def test_fail_to_create_volume_with_all_numberic_label():
    result = exec_failing_test_command(
        BASE_CMDS["volumes"]
        + [
            "create",
            "--label",
            "11111",
            "--region",
            "us-ord",
            "--size",
            "10",
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 400" in result
    assert "label	Must begin with a letter" in result


def test_list_volume(volume_instance_id):
    result = exec_test_command(
        BASE_CMDS["volumes"]
        + [
            "list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id,label,status,region,size,linode_id,linode_label",
        ]
    )
    assert re.search(
        "[0-9]+,[A-Za-z0-9-]+,(creating|active|offline),[A-Za-z0-9-]+,[0-9]+,,",
        result,
    )


@pytest.mark.smoke
def test_view_single_volume(volume_instance_id):
    volume_id = volume_instance_id
    result = exec_test_command(
        BASE_CMDS["volumes"]
        + [
            "view",
            volume_id,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id,label,size,region",
        ]
    )

    assert re.search(volume_id + ",[A-Za-z0-9-]+,[0-9]+,[a-z-]+", result)


def test_update_volume_label(volume_instance_id):
    volume_id = volume_instance_id
    new_unique_label = "label-" + get_random_text(5)
    result = exec_test_command(
        BASE_CMDS["volumes"]
        + [
            "update",
            volume_id,
            "--label",
            new_unique_label,
            "--format",
            "label",
            "--text",
            "--no-headers",
        ]
    )

    assert new_unique_label in result


def test_add_new_tag_to_volume(volume_instance_id):
    unique_tag = get_random_text(5) + "-tag"
    volume_id = volume_instance_id
    result = exec_test_command(
        BASE_CMDS["volumes"]
        + [
            "update",
            volume_id,
            "--tag",
            unique_tag,
            "--format",
            "tags",
            "--text",
            "--no-headers",
        ]
    )

    assert unique_tag in result


def test_view_tags_attached_to_volume(volume_instance_id):
    volume_id = volume_instance_id
    exec_test_command(
        BASE_CMDS["volumes"]
        + ["view", volume_id, "--format", "tags", "--text", "--no-headers"]
    )


def test_fail_to_update_volume_size(volume_instance_id):
    volume_id = volume_instance_id
    os.system(
        "linode-cli volumes update --size=15 "
        + volume_id
        + " 2>&1 | tee /tmp/output_file.txt"
    )

    result = os.popen("cat /tmp/output_file.txt").read()

    assert (
        "linode-cli volumes update: error: unrecognized arguments: --size=15"
        in result
    )
