import re
import time

import pytest

from tests.integration.helpers import (
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
)
from tests.integration.linodes.helpers_linodes import DEFAULT_RANDOM_PASS

BASE_CMD = ["linode-cli", "stackscripts"]
DEF_LABEL = "stack_script_" + str(int(time.time()))


def get_linode_image_lists():
    all_images = (
        (
            exec_test_command(
                [
                    "linode-cli",
                    "images",
                    "list",
                    "--format",
                    "id",
                    "--text",
                    "--no-headers",
                ]
            )
        )
        .stdout.decode()
        .rstrip()
    )

    images = re.findall("linode/[^\s]+", all_images)

    return images


@pytest.fixture(scope="package", autouse=True)
def create_stackscript():
    result = exec_test_command(
        BASE_CMD
        + [
            "create",
            "--script",
            "#!/bin/bash \n $EXAMPLE_SCRIPT",
            "--image",
            "linode/debian9",
            "--label",
            DEF_LABEL,
            "--is_public=false",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()

    assert re.search(
        "[0-9]+,.*,"
        + DEF_LABEL
        + ",linode/debian9,False,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+",
        result,
    )

    stackscript_id = result.split(",")[0]

    yield stackscript_id

    delete_target_id(target="stackscripts", id=stackscript_id)


def test_list_stackscripts():
    result = exec_test_command(BASE_CMD + ["list", "--text"]).stdout.decode()
    assert "id	username	label	images	is_public	created	updated" in result

    result = exec_test_command(
        BASE_CMD
        + [
            "list",
            "--text",
            "--no-headers",
            "--format",
            "id,username,is_public",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()

    output = result.splitlines()

    assert re.search("[0-9]+,([A-z]|[0-9])+,True", output[0])


def test_create_stackscript_fails_without_image():
    result = exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--script",
            "echo",
            "--label",
            "testfoo",
            "--is_public=false",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).stderr.decode()

    assert "Request failed: 400" in result
    assert "images is required" in result


def test_view_private_stackscript():
    result = exec_test_command(
        BASE_CMD
        + [
            "list",
            "--text",
            "--no-headers",
            "--is_public",
            "false",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()

    assert re.search(
        "[0-9]+,.*,"
        + DEF_LABEL
        + ",linode/debian9,False,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+",
        result,
    )


@pytest.mark.smoke
def test_update_stackscript_compatible_image(create_stackscript):
    images = get_linode_image_lists()
    private_stackscript = create_stackscript
    result = (
        exec_test_command(
            BASE_CMD
            + [
                "update",
                "--images",
                images[0],
                private_stackscript,
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    assert re.search(
        "[0-9]+,.*,stack_script_[0-9]+,"
        + images[0]
        + ",False,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+",
        result,
    )


def test_update_stackscript_to_be_compatible_with_multiple_images(
    create_stackscript,
):
    images = get_linode_image_lists()
    private_stackscript = create_stackscript

    result = exec_test_command(
        BASE_CMD
        + [
            "update",
            "--images",
            images[0],
            "--images",
            images[1],
            private_stackscript,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()
    assert images[0] in result
    assert images[1] in result


def test_fail_to_deploy_stackscript_to_linode_from_incompatible_image(
    create_stackscript,
):
    private_stackscript = create_stackscript
    linode_plan = "g6-standard-1"
    linode_region = "us-east"

    result = exec_failing_test_command(
        [
            "linode-cli",
            "linodes",
            "create",
            "--stackscript_id",
            private_stackscript,
            "--type",
            linode_plan,
            "--image",
            "asdf",
            "--region",
            linode_region,
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            "--no-headers",
            "--text",
        ]
    ).stderr.decode()

    assert "image is not valid" in result
    assert "Request failed: 400" in result


def test_deploy_linode_from_stackscript(create_stackscript):
    private_stackscript = create_stackscript
    images = get_linode_image_lists()
    linode_plan = "g6-standard-1"
    linode_region = "us-east"

    result = exec_test_command(
        [
            "linode-cli",
            "linodes",
            "create",
            "--stackscript_id",
            private_stackscript,
            "--type",
            linode_plan,
            "--image",
            images[0],
            "--region",
            linode_region,
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            "--text",
            "--delimiter",
            ",",
            "--format",
            "id,region,type,image",
            "--no-headers",
        ]
    ).stdout.decode()

    assert re.search(
        "[0-9]+," + linode_region + "," + linode_plan + "," + images[0], result
    )

    linode_id = result.split(",")[0]

    delete_target_id("linodes", linode_id)
