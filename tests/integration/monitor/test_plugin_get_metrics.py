"""
Integration tests for the get_metrics plugin
"""

import os

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (  # pylint: disable=import-error
    exec_failing_test_command,
    exec_test_command,
)

# Base command for monitor-api plugin
BASE_CMD = ["linode-cli", "monitor-api", "get-metrics"]

# Skip decorator for tests that require JWE_TOKEN
# To generate a JWE token, use the Linode Monitor API token endpoint:
#   POST https://api.linode.com/v4beta/monitor/services/{service}/token
#   Authorization: Bearer <your-PAT-token>
#   Body: {"entity_ids": [<entity_id>]}
# Replace {service} with the service name (e.g. dbaas, nodebalancer, netloadbalancer)
# and <entity_id> with the ID of the entity to monitor.
# See: https://www.linode.com/docs/api/monitor/
# Then export the token: export JWE_TOKEN='<token>'
requires_jwe_token = pytest.mark.skipif(
    not os.getenv("JWE_TOKEN"),
    reason=(
        "JWE_TOKEN environment variable not set. "
        "See test file header for instructions on generating a JWE token."
    ),
)


class TestAPIValidation:
    """Tests for local argument and API validation error messages"""

    def test_missing_entity_ids(self):
        """Test that omitting --entity-ids produces the correct error"""
        stderr = exec_failing_test_command(
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
        assert "--entity-ids is required for service 'nodebalancer'" in stderr

    def test_missing_metrics(self):
        """Test that omitting --metrics produces the correct error"""
        stderr = exec_failing_test_command(
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
        assert "--metrics: required" in stderr

    def test_missing_time_params(self):
        """Test that omitting all time params produces the correct error"""
        stderr = exec_failing_test_command(
            BASE_CMD
            + [
                "nodebalancer",
                "--entity-ids",
                "123",
                "--metrics",
                "cpu_usage:avg",
            ],
            expected_code=ExitCodes.REQUEST_FAILED,
        )
        assert "Time duration required" in stderr

    def test_invalid_service(self):
        """Test that an unknown service name hits the API and fails"""
        stderr = exec_failing_test_command(
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
        assert "API request failed" in stderr

    def test_invalid_aggregate_function(self):
        """Test that a metric without an aggregate function produces the correct error"""
        stderr = exec_failing_test_command(
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
        assert "Aggregate function required for metric 'cpu_usage'" in stderr

    def test_invalid_aggregate_function_value(self):
        """Test that an unsupported aggregate function produces the correct error"""
        stderr = exec_failing_test_command(
            BASE_CMD
            + [
                "nodebalancer",
                "--entity-ids",
                "123",
                "--metrics",
                "cpu_usage:invalid_func",
                "--duration",
                "15",
                "--duration-unit",
                "min",
            ],
            expected_code=ExitCodes.REQUEST_FAILED,
        )
        assert "Invalid aggregate function 'invalid_func'" in stderr

    def test_invalid_duration_unit(self):
        """Test that an invalid duration unit produces the correct error"""
        stderr = exec_failing_test_command(
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
        assert "Invalid duration unit 'invalid_unit'" in stderr

    def test_conflicting_time_params(self):
        """Test that combining relative and absolute time params produces the correct error"""
        stderr = exec_failing_test_command(
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
        assert (
            "Cannot specify both relative and absolute time duration" in stderr
        )

    def test_malformed_filters(self):
        """Test that a filter missing the operator field produces the correct error"""
        stderr = exec_failing_test_command(
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
        assert "Invalid filter format" in stderr
        assert "invalid_filter_format" in stderr

    def test_entity_ids_required_for_non_objectstorage(self):
        """Test that omitting --entity-ids for a non-objectstorage service fails"""
        stderr = exec_failing_test_command(
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
        assert "--entity-ids is required for service 'dbaas'" in stderr

    def test_invalid_granularity_unit(self):
        """Test that an invalid granularity unit produces the correct error"""
        stderr = exec_failing_test_command(
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
        assert "Invalid granularity unit 'invalid_unit'" in stderr

    def test_granularity_without_unit(self):
        """Test that --granularity without --granularity-unit produces the correct error"""
        stderr = exec_failing_test_command(
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
        assert (
            "Both --granularity and --granularity-unit must be provided together"
            in stderr
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
