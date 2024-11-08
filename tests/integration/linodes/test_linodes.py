import re
import time

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    assert_headers_in_lines,
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
    get_random_region_with_caps,
)
from tests.integration.linodes.helpers_linodes import (
    BASE_CMD,
    DEFAULT_LABEL,
    DEFAULT_RANDOM_PASS,
    DEFAULT_TEST_IMAGE,
    create_linode,
    wait_until,
)

timestamp = str(time.time_ns())
linode_label = DEFAULT_LABEL + timestamp


@pytest.fixture(scope="package", autouse=True)
def test_linode_instance(linode_cloud_firewall):
    linode_id = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--type",
                "g6-nanode-1",
                "--region",
                "us-ord",
                "--image",
                DEFAULT_TEST_IMAGE,
                "--label",
                linode_label,
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--firewall_id",
                linode_cloud_firewall,
                "--text",
                "--delimiter",
                ",",
                "--no-headers",
                "--format",
                "id",
                "--no-defaults",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture
def test_disk_id(test_linode_instance):
    linode_id = test_linode_instance
    disk_id = (
        exec_test_command(
            BASE_CMD
            + [
                "disks-list",
                linode_id,
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
        .splitlines()
    )
    first_id = disk_id[0].split(",")[0]
    yield first_id


def test_update_linode_with_a_image():
    result = exec_test_command(BASE_CMD + ["update", "--help"]).stdout.decode()

    assert "--image" not in result


@pytest.mark.smoke
def test_create_linodes_with_a_label(linode_with_label):
    result = linode_with_label

    assert re.search(
        "^cli(.*),us-ord,g6-nanode-1," + DEFAULT_TEST_IMAGE, result
    )


@pytest.mark.smoke
def test_view_linode_configuration(test_linode_instance):
    linode_id = test_linode_instance
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
        + linode_label
        + ",us-ord,g6-nanode-1,"
        + DEFAULT_TEST_IMAGE,
        result,
    )


def test_create_linode_with_min_required_props(linode_min_req):
    result = linode_min_req
    assert re.search("[0-9]+,us-ord,g6-nanode-1", result)


def test_create_linodes_fails_without_a_root_pass():
    result = exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--type",
            "g6-nanode-1",
            "--region",
            "us-ord",
            "--image",
            DEFAULT_TEST_IMAGE,
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    ).stderr.decode()
    assert "Request failed: 400" in result
    assert "root_pass	root_pass is required" in result


def test_create_linode_without_image_and_not_boot(linode_wo_image):
    linode_id = linode_wo_image

    wait_until(linode_id=linode_id, timeout=180, status="offline")

    result = exec_test_command(
        BASE_CMD
        + ["view", linode_id, "--format", "status", "--text", "--no-headers"]
    ).stdout.decode()

    assert "offline" in result


def test_list_linodes(test_linode_instance):
    result = exec_test_command(
        BASE_CMD + ["list", "--format", "label", "--text", "--no-headers"]
    ).stdout.decode()
    assert linode_label in result


def test_add_tag_to_linode(test_linode_instance):
    linode_id = test_linode_instance
    unique_tag = "tag" + str(int(time.time()))

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


def list_disk_list(test_linode_instance):
    linode_id = test_linode_instance
    res = (
        exec_test_command(
            BASE_CMD
            + [
                "disks-list",
                linode_id,
                "--text",
                "--delimiter=,",
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["id", "label"]
    assert_headers_in_lines(headers, lines)


def test_disk_view(test_linode_instance, test_disk_id):
    linode_id = test_linode_instance
    disk_id = test_disk_id
    res = (
        exec_test_command(
            BASE_CMD
            + [
                "disk-view",
                linode_id,
                disk_id,
                "--text",
                "--delimiter=,",
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["id", "label"]
    assert_headers_in_lines(headers, lines)
    assert disk_id in res


def test_create_linode_disk_encryption_enabled(linode_cloud_firewall):
    test_region = get_random_region_with_caps(
        required_capabilities=["Linodes", "Disk Encryption"]
    )

    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        disk_encryption=True,
        test_region=test_region,
    )

    res = (
        exec_test_command(
            BASE_CMD
            + ["view", linode_id, "--text", "--delimiter=,", "--format=id,disk_encryption"]
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "disk_encryption"]
    assert_headers_in_lines(headers, res.splitlines())

    assert linode_id in res and "enabled" in res

    delete_target_id(target="linodes", id=linode_id)


def test_create_linode_disk_encryption_disabled(linode_cloud_firewall):
    test_region = get_random_region_with_caps(
        required_capabilities=["Linodes", "Disk Encryption"]
    )

    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        disk_encryption=False,
        test_region=test_region,
    )

    res = (
        exec_test_command(
            BASE_CMD
            + ["view", linode_id, "--text", "--delimiter=,", "--format=id,disk_encryption"]
        )
        .stdout.decode()
        .rstrip()
    )

    headers = ["id", "disk_encryption"]
    assert_headers_in_lines(headers, res.splitlines())

    assert linode_id in res and "disabled" in res

    delete_target_id(target="linodes", id=linode_id)
