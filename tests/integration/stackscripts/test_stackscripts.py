import re

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
)
from tests.integration.linodes.helpers import DEFAULT_RANDOM_PASS

DEF_LABEL = "stack_script_" + get_random_text(5)


@pytest.fixture(scope="package", autouse=True)
def test_stackscript_id():
    result = exec_test_command(
        BASE_CMDS["stackscripts"]
        + [
            "create",
            "--script",
            '#!/bin/bash\n# <UDF name="foo" Label="foo" example="bar" />\n $EXAMPLE_SCRIPT',
            "--image",
            "linode/debian10",
            "--label",
            DEF_LABEL,
            "--is_public=false",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    )

    assert re.search(
        "[0-9]+,.*,"
        + DEF_LABEL
        + ",linode/debian10,False,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+",
        result,
    )

    stackscript_id = result.split(",")[0]

    yield stackscript_id

    delete_target_id(target="stackscripts", id=stackscript_id)


def test_list_stackscripts():
    result = exec_test_command(BASE_CMDS["stackscripts"] + ["list", "--text"])
    assert "id	username	label	images	is_public	created	updated" in result

    result = exec_test_command(
        BASE_CMDS["stackscripts"]
        + [
            "list",
            "--text",
            "--no-headers",
            "--format",
            "id,username,is_public",
            "--delimiter",
            ",",
        ]
    )

    output = result.splitlines()

    assert re.search("[0-9]+,([A-z]|[0-9])+,True", output[0])


def test_test_stackscript_id_fails_without_image():
    result = exec_failing_test_command(
        BASE_CMDS["stackscripts"]
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
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "Request failed: 400" in result
    assert "images is required" in result


def test_view_private_stackscript():
    result = exec_test_command(
        BASE_CMDS["stackscripts"]
        + [
            "list",
            "--text",
            "--no-headers",
            "--is_public",
            "false",
            "--delimiter",
            ",",
        ]
    )

    assert re.search(
        "[0-9]+,.*,"
        + DEF_LABEL
        + ",linode/debian10,False,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+",
        result,
    )


@pytest.mark.smoke
def test_update_stackscript_compatible_image(test_stackscript_id):
    images = get_linode_image_lists()
    private_stackscript = test_stackscript_id
    result = exec_test_command(
        BASE_CMDS["stackscripts"]
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

    assert images[0] in result


def test_update_stackscript_to_be_compatible_with_multiple_images(
    test_stackscript_id,
):
    images = get_linode_image_lists()
    private_stackscript = test_stackscript_id

    result = exec_test_command(
        BASE_CMDS["stackscripts"]
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
    )
    assert images[0] in result
    assert images[1] in result


def test_fail_to_deploy_stackscript_to_linode_from_incompatible_image(
    test_stackscript_id,
):
    private_stackscript = test_stackscript_id
    linode_plan = "g6-standard-1"
    linode_region = "us-ord"

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
        ],
        ExitCodes.REQUEST_FAILED,
    )

    assert "image is not valid" in result
    assert "Request failed: 400" in result


def test_deploy_linode_from_stackscript(test_stackscript_id):
    private_stackscript = test_stackscript_id
    images = get_linode_image_lists()
    linode_plan = "g6-standard-1"
    linode_region = "us-ord"

    result = exec_test_command(
        [
            "linode-cli",
            "linodes",
            "create",
            "--stackscript_id",
            private_stackscript,
            "--stackscript_data",
            '{"foo": "bar"}',
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
    )

    assert re.search(
        "[0-9]+," + linode_region + "," + linode_plan + "," + images[0], result
    )

    linode_id = result.split(",")[0]

    delete_target_id("linodes", linode_id)


def get_linode_image_lists():
    all_images = exec_test_command(
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

    images = re.findall(r"linode/[^\s]+", all_images)

    return images
