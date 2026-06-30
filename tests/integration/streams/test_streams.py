from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    assert_help_actions_list,
    exec_failing_test_command,
    exec_test_command,
)


def test_help_streams():
    output = exec_test_command(
        BASE_CMDS["streams"] + ["--help", "--text", "--delimiter=,"]
    )
    actions = [
        "create",
        "delete",
        "destination-create",
        "destination-delete",
        "destination-history-view",
        "destination-update",
        "destination-view",
        "destinations-list",
        "history-view",
        "ls, list",
        "update",
        "view",
    ]
    assert_help_actions_list(actions, output)


def test_create_stream_error():
    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "create",
            "--destinations",
            "1",
            "--label",
            "test",
            "--type",
            "audit_logs",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
        )
    assert "Request failed: 400" in result
    assert "Destination not found" in result


def test_delete_stream_error():
    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "delete",
            "-2",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
        )
    assert "Request failed: 404" in result
    assert "Not found" in result


def test_stream_history_view_error():
    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "history-view",
            "1",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
        )
    assert "Request failed: 404" in result
    assert "Stream not found" in result


def test_list_destinations():
    result = exec_test_command(
        BASE_CMDS["streams"] + ["list", "--delimiter", ",", "--text"]
    )
    lines = result.splitlines()
    headers = [
        "created",
        "created_by",
        "destinations.details.access_key_id", "destinations.details.bucket_name", "destinations.details.host" , "destinations.details.path", "details.cluster_ids",
        "details.is_auto_add_all_clusters_enabled",
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


def test_update_stream_error():
    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "update",
            "1",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
        )
    assert "Request failed: 404" in result
    assert "Stream not found" in result


def test_view_stream_error():
    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "view",
            "1",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
        )
    assert "Request failed: 404" in result
    assert "Stream not found" in result
