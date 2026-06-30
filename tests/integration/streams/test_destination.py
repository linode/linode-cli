from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_failing_test_command,
    exec_test_command,
)
from tests.integration.streams.fixtures import (
    create_destination_akamai_object_storage_type,
    create_object_storage_keys,
)


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
    assert "Request failed: 400" in result
    assert "details,Must be of type Object" in result


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
            "1",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Destination not found" in result


def test_view_delete_destination(create_destination_akamai_object_storage_type):
    result_view = exec_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-view",
            create_destination_akamai_object_storage_type,
            "--delimiter",
            ",",
            "--text",
        ],
    )
    assert result_view == "test"

    exec_test_command(
        BASE_CMDS["streams"]
        + [
            "delete",
            create_destination_akamai_object_storage_type,
            "--delimiter",
            ",",
            "--text",
        ],
    )

    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-view",
            create_destination_akamai_object_storage_type,
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 404" in result
    assert "Not found" in result
