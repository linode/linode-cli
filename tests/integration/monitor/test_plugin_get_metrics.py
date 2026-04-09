"""
Integration tests for the get_metrics plugin
"""

import os

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    exec_failing_test_command,
    exec_test_command,
)

# Base command for monitor-api plugin
BASE_CMD = ["linode-cli", "monitor-api", "get-metrics"]

# Skip decorator for tests that require JWE_TOKEN
requires_jwe_token = pytest.mark.skipif(
    not os.getenv("JWE_TOKEN"),
    reason="JWE_TOKEN environment variable not set",
)


def test_missing_required_args():
    """Test error handling for missing required arguments"""
    # Missing entity-ids
    exec_failing_test_command(
        BASE_CMD
        + [
            "nodebalancer",
            "--metrics",
            "cpu_usage:avg",
            "--duration",
            "15",
            "--duration-unit",
            "min",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )

    # Missing metrics
    exec_failing_test_command(
        BASE_CMD
        + [
            "nodebalancer",
            "--entity-ids",
            "123",
            "--duration",
            "15",
            "--duration-unit",
            "min",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )

    # Missing duration and time parameters
    exec_failing_test_command(
        BASE_CMD
        + ["nodebalancer", "--entity-ids", "123", "--metrics", "cpu_usage:avg"],
        expected_code=ExitCodes.REQUEST_FAILED,
    )


def test_invalid_service():
    """Test error handling for invalid service name"""
    exec_failing_test_command(
        BASE_CMD
        + [
            "invalid_service",
            "--entity-ids",
            "123",
            "--metrics",
            "cpu_usage:avg",
            "--duration",
            "15",
            "--duration-unit",
            "min",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )


def test_invalid_aggregate_function():
    """Test error handling for metrics without aggregate functions"""
    exec_failing_test_command(
        BASE_CMD
        + [
            "nodebalancer",
            "--entity-ids",
            "123",
            "--metrics",
            "cpu_usage",  # Missing :avg
            "--duration",
            "15",
            "--duration-unit",
            "min",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )


def test_invalid_duration_unit():
    """Test handling of invalid duration unit"""
    exec_failing_test_command(
        BASE_CMD
        + [
            "nodebalancer",
            "--entity-ids",
            "123",
            "--metrics",
            "cpu_usage:avg",
            "--duration",
            "15",
            "--duration-unit",
            "invalid_unit",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )


def test_conflicting_time_params():
    """Test handling of conflicting time parameters"""
    exec_failing_test_command(
        BASE_CMD
        + [
            "nodebalancer",
            "--entity-ids",
            "123",
            "--metrics",
            "cpu_usage:avg",
            "--duration",
            "15",
            "--duration-unit",
            "min",
            "--start-time",
            "2025-12-22T00:00:00Z",
            "--end-time",
            "2025-12-22T12:00:00Z",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )


@pytest.mark.smoke
@requires_jwe_token
def test_objstorage_metrics_basic():
    """Test get_metrics with objectstorage service (with authentication)"""
    # Use objectstorage service which doesn't require entity-ids
    output = exec_test_command(
        BASE_CMD
        + [
            "objectstorage",
            "--metrics",
            "obj_requests_num:sum",
            "--duration",
            "15",
            "--duration-unit",
            "min",
            "--entity-region",
            "us-east",
        ]
    )

    print(f"SUCCESS: {output}")
    assert "Fetching metrics" in output or "data" in output.lower()


@requires_jwe_token
def test_obj_metrics_with_filters():
    """Test get_metrics with objectstorage service and filters"""
    output = exec_test_command(
        BASE_CMD
        + [
            "objectstorage",
            "--metrics",
            "obj_requests_num:sum",
            "--duration",
            "30",
            "--duration-unit",
            "min",
            "--entity-region",
            "us-west",
            "--filters",
            "request_type:eq:get",
        ]
    )

    assert "Fetching metrics" in output or "data" in output.lower()


@requires_jwe_token
def test_absolute_time_metrics():
    """Test get_metrics with objectstorage service and absolute time range"""
    output = exec_test_command(
        BASE_CMD
        + [
            "objectstorage",
            "--metrics",
            "obj_requests_num:sum",
            "--start-time",
            "2025-12-22T00:00:00Z",
            "--end-time",
            "2025-12-22T12:00:00Z",
            "--entity-region",
            "us-southeast",
            "--granularity",
            "5",
            "--granularity-unit",
            "min",
        ]
    )

    assert "Fetching metrics" in output or "data" in output.lower()


def test_malformed_filters():
    """Test handling of malformed filter syntax"""
    exec_failing_test_command(
        BASE_CMD
        + [
            "objectstorage",
            "--metrics",
            "obj_requests_num:sum",
            "--duration",
            "15",
            "--duration-unit",
            "min",
            "--filters",
            "invalid_filter_format",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )


def test_invalid_aggregate_function_value():
    """Test handling of invalid aggregate function values"""
    exec_failing_test_command(
        BASE_CMD
        + [
            "nodebalancer",
            "--entity-ids",
            "123",
            "--metrics",
            "cpu_usage:invalid_func",  # Invalid aggregate function
            "--duration",
            "15",
            "--duration-unit",
            "min",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )


def test_entity_ids_required_for_non_objectstorage():
    """Test that entity-ids is required for non-objectstorage services"""
    exec_failing_test_command(
        BASE_CMD
        + [
            "dbaas",
            "--metrics",
            "cpu_usage:avg",
            "--duration",
            "15",
            "--duration-unit",
            "min",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )


def test_invalid_granularity_unit():
    """Test handling of invalid granularity unit"""
    exec_failing_test_command(
        BASE_CMD
        + [
            "nodebalancer",
            "--entity-ids",
            "123",
            "--metrics",
            "cpu_usage:avg",
            "--duration",
            "15",
            "--duration-unit",
            "min",
            "--granularity",
            "5",
            "--granularity-unit",
            "invalid_unit",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )


def test_granularity_without_unit():
    """Test that granularity requires granularity-unit"""
    exec_failing_test_command(
        BASE_CMD
        + [
            "nodebalancer",
            "--entity-ids",
            "123",
            "--metrics",
            "cpu_usage:avg",
            "--duration",
            "15",
            "--duration-unit",
            "min",
            "--granularity",
            "5",
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )
