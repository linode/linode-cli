import os
import subprocess
from typing import List

import pytest

from tests.integration.helpers import assert_headers_in_lines, exec_test_command

BASE_CMD = ["linode-cli", "regions"]

# Set the console width to 150
env = os.environ.copy()
env["COLUMNS"] = "150"


def exe_test_command(args: List[str]):
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        env=env,
    )
    return process


def test_output():
    process = exe_test_command(["linode-cli", "region-table"])
    output = process.stdout.decode()
    lines = output.split("\n")
    lines = lines[3 : len(lines) - 2]
    for line in lines:
        assert "-" in line
        assert "✔" in line
        assert "│" in line


def test_regions_list():
    res = (
        exec_test_command(BASE_CMD + ["list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["label", "country", "capabilities"]
    assert_headers_in_lines(headers, lines)


@pytest.mark.smoke
def test_regions_list_avail():
    res = (
        exec_test_command(BASE_CMD + ["list-avail", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["region", "plan", "available"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def get_region_id():
    region_id = (
        exec_test_command(
            BASE_CMD
            + [
                "list-avail",
                "--text",
                "--no-headers",
                "--delimiter",
                ",",
                "--format",
                "region",
            ]
        )
        .stdout.decode()
        .rstrip()
        .splitlines()
    )
    first_id = region_id[0]
    yield first_id


@pytest.mark.smoke
def test_regions_view(get_region_id):
    region_id = get_region_id
    res = (
        exec_test_command(
            BASE_CMD + ["view", region_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["label", "country", "capabilities"]
    assert_headers_in_lines(headers, lines)


def test_regions_view_avail(get_region_id):
    region_id = get_region_id
    res = (
        exec_test_command(
            BASE_CMD + ["view-avail", region_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()
    headers = ["region", "plan", "available"]
    assert_headers_in_lines(headers, lines)
