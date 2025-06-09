import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_test_command,
)


def test_output():
    output = exec_test_command(["linode-cli", "region-table"])
    lines = output.split("\n")
    lines = lines[3 : len(lines) - 2]
    for line in lines:
        assert "-" in line
        assert "✔" in line
        assert "│" in line


def test_regions_list():
    res = exec_test_command(
        BASE_CMDS["regions"] + ["list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["label", "country", "capabilities"]
    assert_headers_in_lines(headers, lines)


@pytest.mark.smoke
def test_regions_list_avail():
    res = exec_test_command(
        BASE_CMDS["regions"] + ["list-avail", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["region", "plan", "available"]
    assert_headers_in_lines(headers, lines)


@pytest.mark.smoke
def test_regions_view():
    region_id = get_region_id()
    res = exec_test_command(
        BASE_CMDS["regions"] + ["view", region_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["label", "country", "capabilities"]
    assert_headers_in_lines(headers, lines)


def test_regions_view_avail():
    region_id = get_region_id()
    res = exec_test_command(
        BASE_CMDS["regions"]
        + ["view-avail", region_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["region", "plan", "available"]
    assert_headers_in_lines(headers, lines)


def get_region_id():
    region_id = exec_test_command(
        BASE_CMDS["regions"]
        + [
            "list-avail",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "region",
        ]
    ).splitlines()
    first_id = region_id[0]
    return first_id
