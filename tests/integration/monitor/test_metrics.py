import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_failing_test_command,
    exec_test_command,
)


def test_dashboard_list():
    res = exec_test_command(
        BASE_CMDS["monitor"]
        + ["dashboards-list-all", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["created", "id", "label", "service_type", "type", "updated"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def get_dashboard_id():
    dashboard_ids = exec_test_command(
        BASE_CMDS["monitor"]
        + [
            "dashboards-list-all",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    first_id = dashboard_ids[0].split(",")[0]
    yield first_id


def test_dashboard_view(get_dashboard_id):
    dashboard_id = get_dashboard_id
    res = exec_test_command(
        BASE_CMDS["monitor"]
        + [
            "dashboards-view",
            dashboard_id,
            "--text",
            "--delimiter=,",
        ]
    )
    lines = res.splitlines()

    headers = ["created", "id", "label", "service_type", "type", "updated"]
    assert_headers_in_lines(headers, lines)


def test_service_list():
    res = exec_test_command(
        BASE_CMDS["monitor"] + ["service-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["label", "service_type"]
    assert_headers_in_lines(headers, lines)


def test_service_view(get_service_type):
    service_type = get_service_type
    res = exec_test_command(
        BASE_CMDS["monitor"]
        + [
            "service-view",
            service_type,
            "--text",
            "--delimiter=,",
        ]
    )
    lines = res.splitlines()

    headers = ["label", "service_type"]
    assert_headers_in_lines(headers, lines)


def test_dashboard_service_type_list(get_service_type):
    service_type = get_service_type
    res = exec_test_command(
        BASE_CMDS["monitor"]
        + [
            "dashboards-list",
            service_type,
            "--text",
            "--delimiter=,",
        ]
    )
    lines = res.splitlines()

    headers = ["created", "id", "label", "service_type", "type", "updated"]
    assert_headers_in_lines(headers, lines)


def test_metrics_list(get_service_type):
    service_type = get_service_type
    res = exec_test_command(
        BASE_CMDS["monitor"]
        + [
            "metrics-list",
            service_type,
            "--text",
            "--delimiter=,",
        ]
    )
    lines = res.splitlines()

    headers = [
        "available_aggregate_functions",
        "is_alertable",
        "label",
        "metric",
        "metric_type",
        "scrape_interval",
    ]
    assert_headers_in_lines(headers, lines)


def test_try_create_token_with_not_existing_entity(get_service_type):
    service_type = get_service_type
    output = exec_failing_test_command(
        BASE_CMDS["monitor"]
        + [
            "token-get",
            service_type,
            "--entity_ids",
            "99999999999",
            "--text",
            "--delimiter=,",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 403" in output
    assert "The following entity_ids are not valid - [99999999999]" in output
