import os
import re
import time

import pytest

from tests.integration.helpers import (
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "volumes"]
timestamp = str(int(time.time()))
unique_tag = str(int(time.time())) + "-tag"


@pytest.fixture(scope="package")
def setup_test_volumes():
    volume_id = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--label",
                "A" + timestamp,
                "--region",
                "us-east",
                "--size",
                "10",
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield volume_id

    delete_target_id(target="volumes", id=volume_id)


def test_fail_to_create_volume_under_10gb():
    result = exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--label",
            "A" + timestamp,
            "--region",
            "us-east",
            "--size",
            "5",
            "--text",
            "--no-headers",
        ]
    ).stderr.decode()

    if "test" == os.environ.get(
        "TEST_ENVIRONMENT", None
    ) or "dev" == os.environ.get("TEST_ENVIRONMENT", None):
        assert "size	Must be 10-1024" in result
    else:
        assert "size	Must be 10-10240" in result


def test_fail_to_create_volume_without_region():
    result = exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--label",
            "A" + timestamp,
            "--size",
            "10",
            "--text",
            "--no-headers",
        ]
    ).stderr.decode()
    assert "Request failed: 400" in result
    assert "Must provide a region or a Linode ID" in result


def test_fail_to_create_volume_without_label():
    result = exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--region",
            "us-east",
            "--size",
            "10",
            "--text",
            "--no-headers",
        ]
    ).stderr.decode()
    assert "Request failed: 400" in result
    assert "label	label is required" in result


def test_fail_to_create_volume_over_1024gb_in_size():
    result = exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--label",
            "A" + timestamp,
            "--region",
            "us-east",
            "--size",
            "10241",
            "--text",
            "--no-headers",
        ]
    ).stderr.decode()
    if "test" == os.environ.get(
        "TEST_ENVIRONMENT", None
    ) or "dev" == os.environ.get("TEST_ENVIRONMENT", None):
        assert "size	Must be 10-1024" in result
    else:
        assert "size	Must be 10-10240" in result


def test_fail_to_create_volume_with_all_numberic_label():
    result = exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--label",
            "11111",
            "--region",
            "us-east",
            "--size",
            "10",
            "--text",
            "--no-headers",
        ]
    ).stderr.decode()
    assert "Request failed: 400" in result
    assert "label	Must begin with a letter" in result


def test_list_volume(setup_test_volumes):
    result = exec_test_command(
        BASE_CMD + ["list", "--text", "--no-headers", "--delimiter", ","]
    ).stdout.decode()
    assert re.search(
        "[0-9]+,[A-Za-z0-9]+,(creating|active|offline),10,[a-z-]+", result
    )


def test_view_single_volume(setup_test_volumes):
    volume_id = setup_test_volumes
    result = exec_test_command(
        BASE_CMD
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
    ).stdout.decode()

    assert re.search(volume_id + ",[A-Za-z0-9-]+,[0-9]+,[a-z-]+", result)


def test_update_volume_label(setup_test_volumes):
    volume_id = setup_test_volumes
    new_unique_label = "label-" + str(int(time.time()))
    result = exec_test_command(
        BASE_CMD
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
    ).stdout.decode()

    assert new_unique_label in result


def test_add_new_tag_to_volume(setup_test_volumes):
    volume_id = setup_test_volumes
    result = exec_test_command(
        BASE_CMD
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
    ).stdout.decode()

    assert unique_tag in result


def test_view_tags_attached_to_volume(setup_test_volumes):
    volume_id = setup_test_volumes
    exec_test_command(
        BASE_CMD
        + ["view", volume_id, "--format", "tags", "--text", "--no-headers"]
    ).stdout.decode()


def test_fail_to_update_volume_size(setup_test_volumes):
    volume_id = setup_test_volumes
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
