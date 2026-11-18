import json

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_failing_test_command,
    exec_test_command,
)
from tests.integration.streams.fixtures import (  # noqa: F401
    create_destination_akamai_object_storage_type,
    create_object_storage_keys,
)


@pytest.mark.smoke
def test_list_destinations():
    result = exec_test_command(
        BASE_CMDS["streams"]
        + ["destinations-list", "--delimiter", ",", "--text"]
    )
    lines = result.splitlines()
    headers = [
        "created",
        "created_by",
        "details",
        "id",
        "label",
        "status",
        "type",
        "updated",
        "updated_by",
        "version",
    ]
    assert_headers_in_lines(headers, lines)


def test_create_destination_error():
    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-create",
            "--label",
            "test",
            "--type",
            "custom_https",
            "--details",
            "test",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "ambiguous option: --details could match" in result


def test_view_destination_error():
    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-view",
            "1",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Destination not found" in result


def test_destination_history_view_error():
    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-history-view",
            "1",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Destination not found" in result


def test_update_destination_error():
    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-update",
            "1",
            "--details",
            "test",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Destination not found" in result


def test_remove_destination_error():
    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-delete",
            "-1",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Destination not found" in result


def test_create_view_delete_destination(
    create_destination_akamai_object_storage_type,
):
    result_view = exec_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-view",
            str(create_destination_akamai_object_storage_type["id"]),
            "--json",
        ],
    )
    result_view_json = json.loads(result_view)[0]
    assert result_view_json["status"] == "active"
    assert result_view_json["type"] == "akamai_object_storage"
    assert result_view_json["version"] == 1

    result_history_view = exec_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-history-view",
            str(create_destination_akamai_object_storage_type["id"]),
            "--json",
        ],
    )
    result_history_view_json = json.loads(result_history_view)[0]
    assert result_history_view_json["status"] == "active"
    assert result_history_view_json["type"] == "akamai_object_storage"
    assert result_history_view_json["version"] == 1

    exec_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-delete",
            str(create_destination_akamai_object_storage_type["id"]),
            "--delimiter",
            ",",
            "--text",
        ],
    )

    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-view",
            str(create_destination_akamai_object_storage_type["id"]),
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Destination not found" in result
