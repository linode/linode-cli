import json
import os

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    assert_help_actions_list,
    exec_failing_test_command,
    exec_test_command,
)
from tests.integration.streams.fixtures import (  # noqa: F401
    create_destination_akamai_object_storage_type,
    create_object_storage_keys,
    create_stream,
    wait_for_stream_status,
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


@pytest.mark.smoke
def test_list_destinations():
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


@pytest.mark.skipif(
    os.environ.get("RUN_LONG_TESTS", None) != "True",
    reason="Skipping long-running Test, to run set RUN_LONG_TESTS=True",
)
def test_create_view_stream(
    create_stream,
):
    assert create_stream["destinations"][0]["details"]["access_key_id"]
    assert create_stream["destinations"][0]["details"]["bucket_name"]
    assert create_stream["destinations"][0]["details"]["host"]
    assert create_stream["destinations"][0]["details"]["path"]
    assert create_stream["destinations"][0]["type"] == "akamai_object_storage"
    assert create_stream["status"] == "provisioning"
    assert create_stream["type"] == "audit_logs"

    wait_for_stream_status(str(create_stream["id"]), "active")
    result_view = exec_test_command(
        BASE_CMDS["streams"]
        + [
            "view",
            str(create_stream["id"]),
            "--json",
        ],
    )
    result_view_json = json.loads(result_view)[0]
    assert result_view_json["destinations"][0]["details"]["access_key_id"]
    assert result_view_json["destinations"][0]["details"]["bucket_name"]
    assert result_view_json["destinations"][0]["details"]["host"]
    assert result_view_json["destinations"][0]["details"]["path"]
    assert (
        result_view_json["destinations"][0]["type"] == "akamai_object_storage"
    )
    assert result_view_json["status"] == "active"
    assert result_view_json["type"] == "audit_logs"
