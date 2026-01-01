"""
Integration tests for the get_metrics plugin
"""

import json
import os

import pytest

from tests.integration.helpers import (
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
)
from linodecli.exit_codes import ExitCodes

# Base command for get_metrics plugin
BASE_CMD = ["linode-cli", "get_metrics"]


"""
Integration tests for the get_metrics plugin
"""

import os

import pytest

from tests.integration.helpers import (
    exec_failing_test_command,
    exec_test_command,
)
from linodecli.exit_codes import ExitCodes

# Base command for get_metrics plugin
BASE_CMD = ["linode-cli", "get_metrics"]


def test_missing_required_args():
    """Test error handling for missing required arguments"""
    # Missing entity-ids
    exec_failing_test_command(
        BASE_CMD + [
            "nodebalancer",
            "--metrics", "cpu_usage:avg",
            "--duration", "15",
            "--duration-unit", "min"
        ],
        expected_code=ExitCodes.REQUEST_FAILED
    )

    # Missing metrics
    exec_failing_test_command(
        BASE_CMD + [
            "nodebalancer",
            "--entity-ids", "123",
            "--duration", "15",
            "--duration-unit", "min"
        ],
        expected_code=ExitCodes.REQUEST_FAILED
    )

    # Missing duration and time parameters
    exec_failing_test_command(
        BASE_CMD + [
            "nodebalancer",
            "--entity-ids", "123",
            "--metrics", "cpu_usage:avg"
        ],
        expected_code=ExitCodes.REQUEST_FAILED
    )


def test_invalid_service():
    """Test error handling for invalid service name"""
    exec_failing_test_command(
        BASE_CMD + [
            "invalid_service",
            "--entity-ids", "123",
            "--metrics", "cpu_usage:avg",
            "--duration", "15",
            "--duration-unit", "min"
        ],
        expected_code=ExitCodes.REQUEST_FAILED
    )


def test_invalid_aggregate_function():
    """Test error handling for metrics without aggregate functions"""
    exec_failing_test_command(
        BASE_CMD + [
            "nodebalancer",
            "--entity-ids", "123",
            "--metrics", "cpu_usage",  # Missing :avg
            "--duration", "15",
            "--duration-unit", "min"
        ],
        expected_code=ExitCodes.REQUEST_FAILED
    )


def test_invalid_duration_unit():
    """Test handling of invalid duration unit"""
    exec_failing_test_command(
        BASE_CMD + [
            "nodebalancer",
            "--entity-ids", "123",
            "--metrics", "cpu_usage:avg",
            "--duration", "15",
            "--duration-unit", "invalid_unit"
        ],
        expected_code=ExitCodes.REQUEST_FAILED
    )


def test_conflicting_time_params():
    """Test handling of conflicting time parameters"""
    exec_failing_test_command(
        BASE_CMD + [
            "nodebalancer",
            "--entity-ids", "123",
            "--metrics", "cpu_usage:avg",
            "--duration", "15",
            "--duration-unit", "min",
            "--start-time", "2025-12-22T00:00:00Z",
            "--end-time", "2025-12-22T12:00:00Z"
        ],
        expected_code=ExitCodes.REQUEST_FAILED
    )


@pytest.mark.skipif(
    not os.getenv('JWE_TOKEN'),
    reason="JWE_TOKEN environment variable required for monitoring tests"
)
@pytest.mark.smoke
def test_nodebalancer_metrics_basic():
    """Test get_metrics with nodebalancer service (with authentication)"""
    # Use a non-existent entity ID to avoid side effects
    # This will test the complete command flow but fail gracefully
    try:
        output = exec_test_command(BASE_CMD + [
            "nodebalancer",
            "--entity-ids", "999999",
            "--metrics", "nb_ingress_traffic_rate:sum",
            "--duration", "15",
            "--duration-unit", "min"
        ])

        # If it succeeds, check for expected output structure
        assert "Fetching metrics" in output or "data" in output.lower()

    except RuntimeError as e:
        # Expected to fail with entity not found or similar API error
        # Ensure it's not a command structure error
        error_output = str(e)
        assert "API request failed" in error_output or "entity" in error_output.lower()
        # Should not be argument parsing errors
        assert "unrecognized arguments" not in error_output
        assert "invalid choice" not in error_output


@pytest.mark.skipif(
    not os.getenv('JWE_TOKEN'),
    reason="JWE_TOKEN environment variable required for monitoring tests"
)
def test_dbaas_metrics_with_filters():
    """Test get_metrics with dbaas service and filters"""
    try:
        output = exec_test_command(BASE_CMD + [
            "dbaas",
            "--entity-ids", "999999",
            "--metrics", "cpu_usage:avg,memory_usage:max",
            "--duration", "30",
            "--duration-unit", "min",
            "--filters", "node_type:in:primary,secondary",
            "--group-by", "entity_id,node_type"
        ])

        assert "Fetching metrics" in output or "data" in output.lower()

    except RuntimeError as e:
        error_output = str(e)
        assert "API request failed" in error_output or "entity" in error_output.lower()
        assert "unrecognized arguments" not in error_output


@pytest.mark.skipif(
    not os.getenv('JWE_TOKEN'),
    reason="JWE_TOKEN environment variable required for monitoring tests"
)
def test_absolute_time_metrics():
    """Test get_metrics with absolute time range"""
    try:
        output = exec_test_command(BASE_CMD + [
            "linodes",
            "--entity-ids", "999999",
            "--metrics", "cpu_percent:avg",
            "--start-time", "2025-12-22T00:00:00Z",
            "--end-time", "2025-12-22T12:00:00Z",
            "--granularity", "5",
            "--granularity-unit", "min"
        ])

        assert "Fetching metrics" in output or "data" in output.lower()

    except RuntimeError as e:
        error_output = str(e)
        assert "API request failed" in error_output or "entity" in error_output.lower()
        assert "unrecognized arguments" not in error_output


@pytest.mark.skipif(
    not os.getenv('JWE_TOKEN'),
    reason="JWE_TOKEN environment variable required for monitoring tests"
)
def test_multiple_entity_ids():
    """Test get_metrics with multiple entity IDs"""
    try:
        output = exec_test_command(BASE_CMD + [
            "nodebalancer",
            "--entity-ids", "999999,888888,777777",
            "--metrics", "nb_ingress_traffic_rate:sum,nb_egress_traffic_rate:avg",
            "--duration", "1",
            "--duration-unit", "hr",
            "--granularity", "15",
            "--granularity-unit", "min"
        ])

        assert "Fetching metrics" in output or "data" in output.lower()

    except RuntimeError as e:
        error_output = str(e)
        assert "API request failed" in error_output or "entity" in error_output.lower()
        assert "unrecognized arguments" not in error_output


@pytest.mark.skipif(
    not os.getenv('JWE_TOKEN'),
    reason="JWE_TOKEN environment variable required for monitoring tests"
)
def test_complex_filters():
    """Test get_metrics with complex filter combinations"""
    try:
        output = exec_test_command(BASE_CMD + [
            "dbaas",
            "--entity-ids", "999999",
            "--metrics", "cpu_usage:avg,memory_usage:avg,connections:count",
            "--duration", "2",
            "--duration-unit", "hr",
            "--filters", "node_type:in:primary,secondary;status:eq:active;environment:ne:test",
            "--group-by", "entity_id,node_type,environment",
            "--granularity", "30",
            "--granularity-unit", "min"
        ])

        assert "Fetching metrics" in output or "data" in output.lower()

    except RuntimeError as e:
        error_output = str(e)
        assert "API request failed" in error_output or "entity" in error_output.lower()
        assert "unrecognized arguments" not in error_output


def test_missing_token_error():
    """Test error handling when JWE_TOKEN is missing"""
    # Temporarily remove token
    original_token = os.getenv('JWE_TOKEN')
    if 'JWE_TOKEN' in os.environ:
        del os.environ['JWE_TOKEN']

    try:
        exec_failing_test_command(
            BASE_CMD + [
                "nodebalancer",
                "--entity-ids", "123",
                "--metrics", "cpu_usage:avg",
                "--duration", "15",
                "--duration-unit", "min"
            ],
            expected_code=ExitCodes.REQUEST_FAILED
        )
    finally:
        # Restore token
        if original_token:
            os.environ['JWE_TOKEN'] = original_token


def test_empty_entity_ids():
    """Test handling of empty entity IDs"""
    exec_failing_test_command(
        BASE_CMD + [
            "nodebalancer",
            "--entity-ids", "",
            "--metrics", "cpu_usage:avg",
            "--duration", "15",
            "--duration-unit", "min"
        ],
        expected_code=ExitCodes.REQUEST_FAILED
    )


def test_malformed_filters():
    """Test handling of malformed filter syntax"""
    exec_failing_test_command(
        BASE_CMD + [
            "dbaas",
            "--entity-ids", "123",
            "--metrics", "cpu_usage:avg",
            "--duration", "15",
            "--duration-unit", "min",
            "--filters", "invalid_filter_format"
        ],
        expected_code=ExitCodes.REQUEST_FAILED
    )


def test_service_validation():
    """Test that valid services are recognized correctly"""
    valid_services = ["nodebalancer", "netloadbalancer", "linodes", "dbaas"]

    for service in valid_services:
        # This should fail due to missing authentication, not service validation
        try:
            exec_failing_test_command(
                BASE_CMD + [
                    service,
                    "--entity-ids", "123",
                    "--metrics", "cpu_usage:avg",
                    "--duration", "15",
                    "--duration-unit", "min"
                ],
                expected_code=ExitCodes.REQUEST_FAILED
            )
        except AssertionError as e:
            # If it fails with wrong exit code, check it's not service validation error
            error_msg = str(e).lower()
            assert "invalid choice" not in error_msg
            assert f"invalid choice: '{service}'" not in error_msg
