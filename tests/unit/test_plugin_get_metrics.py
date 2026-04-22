"""Unit tests for the monitor-api plugin."""

from importlib import import_module
from unittest.mock import Mock, patch

import pytest
from pytest import CaptureFixture

# Import the monitor-api module using importlib (hyphens not allowed in regular imports)
monitor_api = import_module("linodecli.plugins.monitor-api")

get_metrics = monitor_api.get_metrics
get_metrics_parser = monitor_api.get_metrics_parser
make_api_request = monitor_api.make_api_request
print_metrics_response = monitor_api.print_metrics_response
MetricsConfig = monitor_api.MetricsConfig


class TestAPIRequest:
    """Test API request functionality"""

    def test_make_api_request_success(self):
        """Test successful API request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'{"data": {"test": "data"}}'
        mock_response.json.return_value = {"data": {"test": "data"}}

        with patch.object(
            monitor_api.requests, "post", return_value=mock_response
        ) as mock_post:
            status_code, result = make_api_request(
                "nodebalancer",
                "metrics",
                "POST",
                {"test": "data"},
                "test_token",
            )

            assert status_code == 200
            assert result == {"data": {"test": "data"}}
            mock_post.assert_called_once()

    def test_make_api_request_http_error(self):
        """Test API request with HTTP error"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.content = b"Unauthorized"
        mock_response.json.return_value = {"error": "Unauthorized"}

        with patch.object(
            monitor_api.requests, "post", return_value=mock_response
        ):
            status_code, _ = make_api_request(
                "nodebalancer", "metrics", "POST", {}, "test_token"
            )
            assert status_code == 401


class TestGetMetrics:
    """Test get_metrics function"""

    def test_get_metrics_relative_time(self):
        """Test get_metrics with relative time duration"""
        with patch.object(
            monitor_api,
            "make_api_request",
            return_value=(200, {"data": {"test": "data"}}),
        ):
            with patch.object(
                monitor_api, "print_metrics_response"
            ) as mock_print:
                config = MetricsConfig(
                    service_name="nodebalancer",
                    entity_ids=[123, 456],
                    duration=15,
                    duration_unit="min",
                    start_time=None,
                    end_time=None,
                    metrics=["cpu_usage:avg"],
                    granularity=None,
                    granularity_unit=None,
                    token="test_token",
                )
                get_metrics(config)

                mock_print.assert_called_once_with({"data": {"test": "data"}})

    def test_get_metrics_absolute_time(self):
        """Test get_metrics with absolute time range"""
        with patch.object(
            monitor_api,
            "make_api_request",
            return_value=(200, {"data": {"test": "data"}}),
        ):
            with patch.object(
                monitor_api, "print_metrics_response"
            ) as mock_print:
                config = MetricsConfig(
                    service_name="dbaas",
                    entity_ids=[789],
                    duration=None,
                    duration_unit=None,
                    start_time="2025-12-22T00:00:00Z",
                    end_time="2025-12-22T12:00:00Z",
                    metrics=["memory_usage:max"],
                    granularity=None,
                    granularity_unit=None,
                    token="test_token",
                )
                get_metrics(config)

                mock_print.assert_called_once_with({"data": {"test": "data"}})

    def test_get_metrics_with_filters_and_groupby(self):
        """Test get_metrics with filters and group_by"""
        with patch.object(
            monitor_api,
            "make_api_request",
            return_value=(200, {"data": {"test": "data"}}),
        ):
            with patch.object(
                monitor_api, "print_metrics_response"
            ) as mock_print:
                config = MetricsConfig(
                    service_name="dbaas",
                    entity_ids=[123],
                    duration=1,
                    duration_unit="hr",
                    start_time=None,
                    end_time=None,
                    metrics=["cpu_usage:avg"],
                    granularity=None,
                    granularity_unit=None,
                    filters=[
                        "node_type:in:primary,secondary",
                        "status:eq:active",
                    ],
                    group_by=["entity_id", "node_type"],
                    token="test_token",
                )
                get_metrics(config)

                mock_print.assert_called_once_with({"data": {"test": "data"}})

    def test_get_metrics_api_error(self):
        """Test get_metrics with API error response"""
        with patch.object(
            monitor_api,
            "make_api_request",
            return_value=(401, {"error": "Unauthorized"}),
        ):
            with patch("builtins.print"):
                with patch.object(monitor_api.sys, "exit") as mock_exit:
                    config = MetricsConfig(
                        service_name="nodebalancer",
                        entity_ids=[123],
                        duration=15,
                        duration_unit="min",
                        start_time=None,
                        end_time=None,
                        metrics=["cpu_usage:avg"],
                        granularity=None,
                        granularity_unit=None,
                        token="test_token",
                    )
                    get_metrics(config)

                    mock_exit.assert_called_with(2)  # ExitCodes.REQUEST_FAILED


class TestArgumentParsing:
    """Test argument parsing"""

    def test_get_metrics_parser(self):
        """Test parser creation"""
        parser = get_metrics_parser()

        args = parser.parse_args(
            [
                "get-metrics",
                "nodebalancer",
                "--entity-ids",
                "123,456",
                "--metrics",
                "cpu_usage:avg,memory_usage:max",
                "--duration",
                "15",
                "--duration-unit",
                "min",
            ]
        )

        assert args.command == "get-metrics"
        assert args.service == "nodebalancer"
        assert args.entity_ids == "123,456"
        assert args.metrics == "cpu_usage:avg,memory_usage:max"
        assert args.duration == 15
        assert args.duration_unit == "min"


class TestPrintResponse:
    """Test response printing"""

    def test_print_metrics_response_success(self, capsys: CaptureFixture):
        """Test metrics response printing for successful response"""
        response_data = {
            "status": "success",
            "data": {
                "result": [
                    {
                        "entity_id": 123,
                        "cpu_usage": [
                            {"timestamp": "2025-12-22T10:00:00Z", "value": 45.2}
                        ],
                    }
                ]
            },
            "stats": {"executionTimeMsec": 150, "seriesFetched": 1},
        }

        print_metrics_response(response_data)
        captured = capsys.readouterr()

        # Verify success output
        assert "Series fetched: 1" in captured.out
        assert "Metrics Data:" in captured.out

    def test_print_metrics_response_error(self, capsys: CaptureFixture):
        """Test metrics response printing for error response"""
        response_data = {"status": "error", "error": "Invalid parameters"}

        print_metrics_response(response_data)
        captured = capsys.readouterr()

        # Verify error output
        assert "API returned error status: error" in captured.out
        assert "Error: Invalid parameters" in captured.out

    def test_print_metrics_response_empty(self, capsys: CaptureFixture):
        """Test metrics response printing for empty response"""
        print_metrics_response({})
        captured = capsys.readouterr()

        assert "No response received" in captured.out


class TestAPIValidation:
    """Test API argument and service validation - all tests cover local validation logic"""

    def test_invalid_service(self, capsys: CaptureFixture):
        """Test that a missing service name exits with REQUEST_FAILED and appropriate message"""
        with pytest.raises(SystemExit) as exc_info:
            monitor_api.call(["get-metrics"])
        captured = capsys.readouterr()
        assert exc_info.value.code == monitor_api.ExitCodes.REQUEST_FAILED
        assert "Service name is required" in captured.err

    def test_invalid_aggregate_function(self, capsys: CaptureFixture):
        """Test that a metric without an aggregate function exits with REQUEST_FAILED"""
        with pytest.raises(SystemExit) as exc_info:
            monitor_api.call(
                [
                    "get-metrics",
                    "nodebalancer",
                    "--entity-ids",
                    "123",
                    "--duration",
                    "15",
                    "--duration-unit",
                    "min",
                    "--metrics",
                    "cpu_usage",
                ]
            )
        captured = capsys.readouterr()
        assert exc_info.value.code == monitor_api.ExitCodes.REQUEST_FAILED
        assert (
            "Aggregate function required for metric 'cpu_usage'" in captured.err
        )

    def test_invalid_aggregate_function_value(self, capsys: CaptureFixture):
        """Test that a metric with an unsupported aggregate function exits with REQUEST_FAILED"""
        with pytest.raises(SystemExit) as exc_info:
            monitor_api.call(
                [
                    "get-metrics",
                    "nodebalancer",
                    "--entity-ids",
                    "123",
                    "--duration",
                    "15",
                    "--duration-unit",
                    "min",
                    "--metrics",
                    "cpu_usage:badagg",
                ]
            )
        captured = capsys.readouterr()
        assert exc_info.value.code == monitor_api.ExitCodes.REQUEST_FAILED
        assert "Invalid aggregate function 'badagg'" in captured.err

    def test_invalid_duration_unit(self, capsys: CaptureFixture):
        """Test that an invalid duration unit exits with REQUEST_FAILED and names the bad unit"""
        with pytest.raises(SystemExit) as exc_info:
            monitor_api.call(
                [
                    "get-metrics",
                    "nodebalancer",
                    "--entity-ids",
                    "123",
                    "--duration",
                    "15",
                    "--duration-unit",
                    "seconds",
                    "--metrics",
                    "cpu_usage:avg",
                ]
            )
        captured = capsys.readouterr()
        assert exc_info.value.code == monitor_api.ExitCodes.REQUEST_FAILED
        assert "Invalid duration unit 'seconds'" in captured.err

    def test_conflicting_time_params(self, capsys: CaptureFixture):
        """Test that combining relative and absolute time params exits with REQUEST_FAILED"""
        with pytest.raises(SystemExit) as exc_info:
            monitor_api.call(
                [
                    "get-metrics",
                    "nodebalancer",
                    "--entity-ids",
                    "123",
                    "--duration",
                    "15",
                    "--duration-unit",
                    "min",
                    "--start-time",
                    "2025-12-22T00:00:00Z",
                    "--end-time",
                    "2025-12-22T12:00:00Z",
                    "--metrics",
                    "cpu_usage:avg",
                ]
            )
        captured = capsys.readouterr()
        assert exc_info.value.code == monitor_api.ExitCodes.REQUEST_FAILED
        assert (
            "Cannot specify both relative and absolute time duration"
            in captured.err
        )

    def test_malformed_filters(self, capsys: CaptureFixture):
        """Test that a filter missing the operator field exits with REQUEST_FAILED"""
        with pytest.raises(SystemExit) as exc_info:
            monitor_api.call(
                [
                    "get-metrics",
                    "nodebalancer",
                    "--entity-ids",
                    "123",
                    "--duration",
                    "15",
                    "--duration-unit",
                    "min",
                    "--metrics",
                    "cpu_usage:avg",
                    "--filters",
                    "dimension:value",
                ]
            )
        captured = capsys.readouterr()
        assert exc_info.value.code == monitor_api.ExitCodes.REQUEST_FAILED
        assert "Invalid filter format" in captured.err
        assert "dimension:value" in captured.err

    def test_entity_ids_required_for_non_objectstorage(
        self, capsys: CaptureFixture
    ):
        """Test that --entity-ids is required for non-objectstorage service."""
        with pytest.raises(SystemExit) as exc_info:
            monitor_api.call(
                [
                    "get-metrics",
                    "nodebalancer",
                    "--duration",
                    "15",
                    "--duration-unit",
                    "min",
                    "--metrics",
                    "cpu_usage:avg",
                ]
            )
        captured = capsys.readouterr()
        assert exc_info.value.code == monitor_api.ExitCodes.REQUEST_FAILED
        assert (
            "--entity-ids is required for service 'nodebalancer'"
            in captured.err
        )

    def test_invalid_granularity_unit(self, capsys: CaptureFixture):
        """Test that an invalid granularity unit exits with REQUEST_FAILED and names the bad unit"""
        with pytest.raises(SystemExit) as exc_info:
            monitor_api.call(
                [
                    "get-metrics",
                    "nodebalancer",
                    "--entity-ids",
                    "123",
                    "--duration",
                    "15",
                    "--duration-unit",
                    "min",
                    "--metrics",
                    "cpu_usage:avg",
                    "--granularity",
                    "10",
                    "--granularity-unit",
                    "seconds",
                ]
            )
        captured = capsys.readouterr()
        assert exc_info.value.code == monitor_api.ExitCodes.REQUEST_FAILED
        assert "Invalid granularity unit 'seconds'" in captured.err

    def test_granularity_without_unit(self, capsys: CaptureFixture):
        """Test that --granularity without --granularity-unit exits with REQUEST_FAILED"""
        with pytest.raises(SystemExit) as exc_info:
            monitor_api.call(
                [
                    "get-metrics",
                    "nodebalancer",
                    "--entity-ids",
                    "123",
                    "--duration",
                    "15",
                    "--duration-unit",
                    "min",
                    "--metrics",
                    "cpu_usage:avg",
                    "--granularity",
                    "10",
                ]
            )
        captured = capsys.readouterr()
        assert exc_info.value.code == monitor_api.ExitCodes.REQUEST_FAILED
        assert (
            "Both --granularity and --granularity-unit must be provided together"
            in captured.err
        )

    def test_get_metrics_success_with_filter_and_region_assertions(
        self, capsys: CaptureFixture
    ):
        """Test successful metrics fetch - validate filters, region, and time in the API payload"""
        mock_response = {
            "status": "success",
            "data": {
                "result": [{"entity_id": 123, "values": [[1640000000, "45.2"]]}]
            },
            "stats": {"executionTimeMsec": 100, "seriesFetched": 1},
        }
        with patch.object(
            monitor_api, "make_api_request", return_value=(200, mock_response)
        ) as mock_api:
            config = MetricsConfig(
                service_name="dbaas",
                entity_ids=[123],
                duration=None,
                duration_unit=None,
                start_time="2025-12-22T00:00:00Z",
                end_time="2025-12-22T12:00:00Z",
                metrics=["cpu_usage:avg"],
                granularity=None,
                granularity_unit=None,
                filters=["node_type:eq:primary"],
                entity_region="us-east-1",
                token="test_token",
            )
            get_metrics(config)

        captured = capsys.readouterr()
        assert "Fetching metrics" in captured.out

        payload = mock_api.call_args[0][3]
        assert payload["absolute_time_duration"] == {
            "start": "2025-12-22T00:00:00Z",
            "end": "2025-12-22T12:00:00Z",
        }
        assert payload["entity_region"] == "us-east-1"
        assert {
            "dimension_label": "node_type",
            "operator": "eq",
            "value": "primary",
        } in payload["filters"]
