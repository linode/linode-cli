from importlib import import_module
from unittest.mock import Mock, patch

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
