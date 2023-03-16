import pytest
import os

from tests.integration.helpers import exec_failing_test_command, exec_test_command
from tests.integration.linodes.helpers_linodes import (
    DEFAULT_RANDOM_PASS,
    remove_linodes,
)

BASE_CMD = ["linode-cli", "stackscripts"]


@pytest.fixture(scope="session", autouse=True)
def setup_test_stackscripts():
    remove_linodes()
    yield "setup"
    delete_stackscript_and_teardown_linode()


def get_linode_image_lists():
    images = os.popen(
        'LINODE_CLI_TOKEN=$LINODE_CLI_TOKEN linode-cli images list --format id --text --no-headers | egrep "linode\/.*"'
    ).read()

    return images.splitlines()


def get_private_stackscript():
    private_stackscript = (
        exec_test_command(
            BASE_CMD
            + [
                "list",
                "--is_public",
                "false",
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    return private_stackscript.splitlines()


def delete_stackscript_and_teardown_linode():
    private_stackscript = get_private_stackscript()
    for sc_id in private_stackscript:
        exec_test_command(BASE_CMD + ["delete", sc_id])
    remove_linodes()


@pytest.fixture(scope="session", autouse=True)
def test_create_stackscript():
    result = exec_test_command(
        BASE_CMD
        + [
            "create",
            "--script",
            "#!/bin/bash \n $EXAMPLE_SCRIPT",
            "--image",
            "linode/debian9",
            "--label",
            "testfoo",
            "--is_public=false",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()

    assert re.search(
        "[0-9]+,.*,testfoo,linode/debian9,False,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+",
        result,
    )


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


def test_create_stackscrip_fails_without_image():
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
        "[0-9]+,.*,testfoo,linode/debian9,False,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+",
        result,
    )


def test_update_stackscript_compatible_image():
    images = get_linode_image_lists()
    private_stackscript = get_private_stackscript()
    result = exec_test_command(
        BASE_CMD
        + [
            "update",
            "--images",
            images[0],
            private_stackscript[0],
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()

    assert re.search(
        "[0-9]+,.*,testfoo,"
        + images[0]
        + ",False,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+,[0-9]+-[0-9]+-[0-9]+T[0-9]+:[0-9]+:[0-9]+",
        result,
    )


@pytest.fixture(scope="session")
def test_update_stackscript_to_be_compatible_with_multiple_images():
    images = get_linode_image_lists()
    private_stackscript = get_private_stackscript()

    result = exec_test_command(
        BASE_CMD
        + [
            "update",
            "--images",
            images[0],
            "--images",
            images[1],
            private_stackscript[0],
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
        ]
    ).stdout.decode()
    assert images[0] in result
    assert images[1] in result


def test_fail_to_deploy_stackscript_to_linode_from_incompatible_image():
    private_stackscript = get_private_stackscript()
    linode_plan = "g6-standard-1"
    linode_region = "us-east"

    result = exec_failing_test_command(
        [
            "linode-cli",
            "linodes",
            "create",
            "--stackscript_id",
            private_stackscript[0],
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


@pytest.mark.usefixtures(
    "test_update_stackscript_to_be_compatible_with_multiple_images"
)
def test_deploy_linode_from_stackscript():
    private_stackscript = get_private_stackscript()
    images = get_linode_image_lists()
    linode_plan = "g6-standard-1"
    linode_region = "us-east"

    result = exec_test_command(
        [
            "linode-cli",
            "linodes",
            "create",
            "--stackscript_id",
            private_stackscript[0],
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
