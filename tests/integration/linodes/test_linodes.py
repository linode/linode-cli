import logging
import pytest
from tests.integration.linodes.helpers_linodes import *


@pytest.fixture(scope="session", autouse=True)
def setup_linodes():
    try:
        # create one linode with default label for some tests
        linode_id = (
            exec_test_command(
                BASE_CMD
                + [
                    "create",
                    "--type",
                    "g6-standard-2",
                    "--region",
                    "us-east",
                    "--image",
                    DEFAULT_TEST_IMAGE,
                    "--label",
                    DEFAULT_LABEL,
                    "--root_pass",
                    DEFAULT_RANDOM_PASS,
                    "--text",
                    "--delimiter",
                    ",",
                    "--no-headers",
                    "--format",
                    "label,region,type,image",
                    "--no-defaults",
                    "--format",
                    "id",
                ]
            )
            .stdout.decode()
            .rstrip()
        )
    except:
        logging.exception("Failed to create default linode in setup..")
    yield linode_id
    try:
        # clean up
        remove_linodes()
    except:
        logging.exception("Failed removing all linodes..")


def test_update_linode_with_a_image():
    result = exec_test_command(BASE_CMD + ["update", "--help"]).stdout.decode()

    assert "--image" not in result


def test_create_linodes_with_a_label():
    result = exec_test_command(
        BASE_CMD
        + [
            "create",
            "--type",
            "g6-standard-2",
            "--region",
            "us-east",
            "--image",
            DEFAULT_TEST_IMAGE,
            "--label",
            "cli-1",
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format",
            "label,region,type,image",
            "--no-defaults",
        ]
    ).stdout.decode()

    print(result)
    assert re.search(
        "cli-1,us-east,g6-standard-2," + DEFAULT_TEST_IMAGE, result
    )


def test_view_linode_configuration(setup_linodes):
    linode_id = setup_linodes
    result = exec_test_command(
        BASE_CMD
        + [
            "view",
            linode_id,
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format",
            "id,label,region,type,image",
            "--no-defaults",
        ]
    ).stdout.decode()

    assert re.search(
        linode_id
        + ","
        + DEFAULT_LABEL
        + ",us-east,g6-standard-2,"
        + DEFAULT_TEST_IMAGE,
        result,
    )


def test_create_linode_with_min_required_props():
    result = exec_test_command(
        BASE_CMD
        + [
            "create",
            "--type",
            "g6-standard-2",
            "--region",
            "us-east",
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            "--no-defaults",
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format",
            "id,region,type",
        ]
    ).stdout.decode()
    assert re.search("[0-9]+,us-east,g6-standard-2", result)


def test_create_linodes_fails_without_a_root_pass():
    result = exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--type",
            "g6-standard-2",
            "--region",
            "us-east",
            "--image",
            DEFAULT_TEST_IMAGE,
            "--text",
            "--no-headers",
        ]
    ).stderr.decode()
    assert "Request failed: 400" in result
    assert "root_pass	root_pass is required" in result


def test_create_linode_without_image_and_not_boot():
    linode_type = (
        os.popen(
            "linode-cli linodes types --text --no-headers --format=id | xargs | awk '{ print $1 }'"
        )
        .read()
        .rstrip()
    )
    linode_region = (
        os.popen(
            "linode-cli regions list --format=id  --text --no-headers | xargs | awk '{ print $1 }'"
        )
        .read()
        .rstrip()
    )

    exec_test_command(
        BASE_CMD
        + [
            "create",
            "--no-defaults",
            "--label",
            "cli-2",
            "--type",
            linode_type,
            "--region",
            linode_region,
            "--root_pass",
            DEFAULT_RANDOM_PASS,
        ]
    ).stdout.decode()

    linode_id = (
        exec_test_command(
            BASE_CMD
            + [
                "list",
                "--label",
                "cli-2",
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    wait_until(linode_id=linode_id, timeout=180, status="offline")

    result = exec_test_command(
        BASE_CMD
        + ["view", linode_id, "--format", "status", "--text", "--no-headers"]
    ).stdout.decode()

    assert "offline" in result


def test_list_linodes(setup_linodes):
    result = exec_test_command(
        BASE_CMD + ["list", "--format", "label", "--text", "--no-headers"]
    ).stdout.decode()
    assert DEFAULT_LABEL in result


def test_add_tag_to_linode(setup_linodes):
    linode_id = setup_linodes
    unique_tag = str(int(time.time())) + "tag"

    result = exec_test_command(
        BASE_CMD
        + [
            "update",
            linode_id,
            "--tags",
            unique_tag,
            "--format",
            "tags",
            "--text",
            "--no-headers",
        ]
    ).stdout.decode()

    assert unique_tag in result
