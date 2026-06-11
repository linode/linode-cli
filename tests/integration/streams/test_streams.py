from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    assert_help_actions_list,
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
)
from tests.integration.streams.fixtures import (
    create_destination_akamai_object_storage_type,
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


def test_list_destinations(create_destination_akamai_object_storage_type):
    result = exec_test_command(
        BASE_CMDS["streams"] + ["destinations-list", "--delimiter", ",", "--text"]
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


def test_create_view_update_remove_destination():
    label = get_random_text(8) + "_destination_cli_test"
    result_create_stream = exec_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-create",
            "--details",
            "--label",
            label,
            "--type",
            "--delimiter",
            ",",
            "--text",
        ]
    ).splitlines()
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
    assert_headers_in_lines(headers, result_create_stream)
    assert label in result_create_stream[1]

    result_view = exec_test_command(
        BASE_CMDS["streams"]
        + ["destination-view", result_create_stream[0], "--delimiter", ",", "--text"]
    ).splitlines()
    assert_headers_in_lines(headers, result_view)
    assert label in result_view[1]

    result_update_stream = exec_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-update",
            result_create_stream[0],
            "--delimiter",
            ",",
            "--text",
        ]
    ).splitlines()
    assert_headers_in_lines(headers, result_update_stream)

    exec_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-delete",
            result_create_stream[0],
            "--delimiter",
            ",",
            "--text",
        ]
    ).splitlines()

    exec_test_command(
        BASE_CMDS["streams"]
        + ["destination-view", result_create_stream[0], "--delimiter", ",", "--text"]
    )


def test_list_streams():
    result = exec_test_command(
        BASE_CMDS["streams"] + ["list", "--delimiter", ",", "--text"]
    )
    lines = result.splitlines()
    headers = [
        "created",
        "created_by",
        "destinations.details.access_key_id",
        "destinations.details.bucket_name",
        "destinations.details.host",
        "destinations.details.path",
        "details.cluster_ids",
        "details.is_auto_add_all_clusters_enabled",
        "id",
        "label",
        "status",
        "type",
        "updated",
        "updated_by",
        "version",
    ]
    assert_headers_in_lines(headers, lines)


def test_create_stream_invalid_destination_error():
    result = exec_failing_test_command(
        BASE_CMDS["streams"]
        + [
            "create",
            "--label",
            "test",
            "--type",
            "audit_logs",
            "--destinations",
            "12341234",
            "--delimiter",
            ",",
            "--text",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
        )
    assert "Request failed: 400" in result
    assert "Destination not found" in result
