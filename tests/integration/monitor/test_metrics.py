import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
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
    dashboard_id = get_service_type
    res = exec_test_command(
        BASE_CMDS["monitor"]
        + [
            "service-view",
            dashboard_id,
            "--text",
            "--delimiter=,",
        ]
    )
    lines = res.splitlines()

    headers = ["label", "service_type"]
    assert_headers_in_lines(headers, lines)


def test_dashboard_service_type_list(get_service_type):
    dashboard_id = get_service_type
    res = exec_test_command(
        BASE_CMDS["monitor"]
        + [
            "dashboards-list",
            dashboard_id,
            "--text",
            "--delimiter=,",
        ]
    )
    lines = res.splitlines()

    headers = ["created", "id", "label", "service_type", "type", "updated"]
    assert_headers_in_lines(headers, lines)


def test_metrics_list(get_service_type):
    dashboard_id = get_service_type
    res = exec_test_command(
        BASE_CMDS["monitor"]
        + [
            "metrics-list",
            dashboard_id,
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
