"""
This plugin provides access to the Linode Monitor API.

Commands:
    get-metrics: Query metrics from the monitoring service for various services.

Usage:
    linode-cli monitor-api get-metrics <service> [options]
"""

import json
import os
import sys
from argparse import ArgumentParser
from dataclasses import dataclass
from typing import List, Optional

import requests

from linodecli.exit_codes import ExitCodes
from linodecli.help_formatter import SortingHelpFormatter
from linodecli.helpers import register_debug_arg

PLUGIN_BASE = "linode-cli monitor-api"

# API Configuration
API_BASE_URL = "https://monitor-api.linode.com"
API_VERSION = "v2"


def get_auth_token():
    """
    Get authentication token from JWE_TOKEN environment variable
    Raises an error if the environment variable is not set
    """
    token = os.getenv("JWE_TOKEN")
    if not token:
        raise ValueError(
            "JWE_TOKEN environment variable is required but not set. "
            "Please set it with: export JWE_TOKEN='your_token_here'"
        )
    return token



# Aggregate functions
AGGREGATE_FUNCTIONS = ["sum", "avg", "max", "min", "count"]


@dataclass
class MetricsConfig:
    """Configuration for metrics request"""
    service_name: str
    entity_ids: List
    duration: Optional[int]
    duration_unit: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    metrics: List[str]
    granularity: Optional[int]
    granularity_unit: Optional[str]
    filters: Optional[List[str]] = None
    group_by: Optional[List[str]] = None
    entity_region: Optional[str] = None
    associated_entity_region: Optional[str] = None
    token: Optional[str] = None


def make_api_request(
    service_name: str,
    endpoint: str,
    method: str = "POST",
    data: Optional[dict] = None,
    token: Optional[str] = None,
) -> tuple:
    """
    Make an API request to the monitoring service

    Args:
        service_name: The service name (nodebalancer, netloadbalancer, etc.)
        endpoint: The API endpoint to call
        method: HTTP method 
        data: Request payload for POST requests
        token: Bearer token for authentication

    Returns:
        Tuple of (status_code, response_data)
    """
    url = f"{API_BASE_URL}/{API_VERSION}/monitor/services/{service_name}/{endpoint}"

    headers = {
        "Authorization": f"Bearer {token or get_auth_token()}",
        "Authentication-type": "jwe",
        "Pragma": "akamai-x-get-extracted-values",
        "Content-Type": "application/json",
    }

    try:
        if method.upper() == "POST":
            response = requests.post(
                url, headers=headers, json=data, timeout=30, verify=True
            )
        else:
            response = requests.get(
                url, headers=headers, timeout=30, verify=True
            )

        # Try to parse JSON response, fallback to text if it fails
        try:
            response_data = response.json() if response.content else {}
        except json.JSONDecodeError:
            response_data = {"error": f"Non-JSON response: {response.text}"}

        return response.status_code, response_data
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}", file=sys.stderr)
        return 500, {"error": str(e)}


def parse_metrics(metrics: List[str]) -> List[dict]:
    """Parse metrics with mandatory aggregate functions"""
    parsed_metrics = []
    for metric in metrics:
        if ":" in metric:
            metric_name, agg_func = metric.split(":", 1)
            parsed_metrics.append(
                {"aggregate_function": agg_func, "name": metric_name.strip()}
            )
        else:
            print(
                f"Aggregate function required for metric '{metric}'",
                file=sys.stderr,
            )
            print(
                f"Format: 'metric_name:function' where function is one of: "
                f"{', '.join(AGGREGATE_FUNCTIONS)}",
                file=sys.stderr,
            )
            sys.exit(ExitCodes.REQUEST_FAILED)
    return parsed_metrics


def build_payload(config: MetricsConfig) -> dict:
    """Build API request payload from configuration"""
    parsed_metrics = parse_metrics(config.metrics)
    payload = {"metrics": parsed_metrics}

    if config.entity_ids:
        payload["entity_ids"] = config.entity_ids
    if config.group_by:
        payload["group_by"] = config.group_by
    if config.entity_region:
        payload["entity_region"] = config.entity_region
    if config.associated_entity_region:
        payload["associated_entity_region"] = config.associated_entity_region

    # Add time duration - either relative or absolute
    if config.start_time and config.end_time:
        payload["absolute_time_duration"] = {
            "start": config.start_time,
            "end": config.end_time,
        }
    elif config.duration is not None and config.duration_unit is not None:
        payload["relative_time_duration"] = {
            "unit": config.duration_unit,
            "value": config.duration,
        }
    else:
        print(
            "Either (--duration and --duration-unit) or "
            "(--start-time and --end-time) must be provided",
            file=sys.stderr,
        )
        sys.exit(ExitCodes.REQUEST_FAILED)

    # Add time_granularity if provided
    if config.granularity is not None and config.granularity_unit is not None:
        payload["time_granularity"] = {
            "unit": config.granularity_unit,
            "value": config.granularity,
        }

    # Add filters if provided
    if config.filters:
        parsed_filters = []
        for filter_str in config.filters:
            parts = filter_str.split(":", 2)
            if len(parts) != 3:
                print(
                    f"Invalid filter format: '{filter_str}'. "
                    "Expected format: 'dimension:operator:value'",
                    file=sys.stderr,
                )
                sys.exit(ExitCodes.REQUEST_FAILED)

            dimension_label, operator, value = parts
            parsed_filters.append(
                {
                    "dimension_label": dimension_label.strip(),
                    "operator": operator.strip(),
                    "value": value.strip(),
                }
            )
        payload["filters"] = parsed_filters

    return payload


def get_metrics(config: MetricsConfig):
    """Get metrics for specified service entities"""
    payload = build_payload(config)

    if config.entity_ids:
        print(f"Fetching metrics for {config.service_name} entities: {config.entity_ids}")
    else:
        print(f"Fetching metrics for {config.service_name} (all entities)")
    print(f"Request payload: {json.dumps(payload, indent=2)}")

    try:
        status, response = make_api_request(
            config.service_name, "metrics", "POST", payload, config.token
        )
    except ValueError as e:
        print(f"Authentication Error: {e}", file=sys.stderr)
        sys.exit(ExitCodes.REQUEST_FAILED)

    if status != 200:
        print(f"API request failed with status {status}", file=sys.stderr)
        print(
            f"Error response: {json.dumps(response, indent=2)}", file=sys.stderr
        )
        print("Exiting due to API error...", file=sys.stderr)
        sys.exit(ExitCodes.REQUEST_FAILED)

    print_metrics_response(response)

def print_metrics_response(data: dict):
    """
    Print metrics data as formatted JSON
    """
    if not data:
        print("No response received")
        return

    if data.get("status") == "success":
        metrics_data = data.get("data", {}).get("result", [])
        stats = data.get("stats", {})

        if not metrics_data:
            print("No metrics data found for the specified parameters")
            print(f"Execution time: {stats.get('executionTimeMsec', 0)}ms")
            print(f"Series fetched: {stats.get('seriesFetched', 0)}")
        else:
            print(f"Series fetched: {stats.get('seriesFetched', 0)}")
            print("\nMetrics Data:")
            print(json.dumps(data.get("data"), indent=2))
    else:
        print(f"API returned error status: {data.get('status', 'unknown')}")
        if "error" in data:
            print(f"Error: {data['error']}")


def print_help(parser: ArgumentParser):
    """
    Print help information
    """
    parser.print_help()

    print("\nExamples:")
    print("  # Get metrics with relative time duration")
    print(
        "  linode-cli monitor-api get-metrics dbaas --entity-ids 123 --duration 15 "
        "--duration-unit min --metrics cpu_usage:avg"
    )

    print(
        "\n  # Get metrics for all entities "
        "(only allowed for objectstorage service)"
    )
    print(
        "  linode-cli monitor-api get-metrics objectstorage --duration 15 "
        "--duration-unit min --metrics obj_requests_num:avg "
        "--entity-region us-east-1"
    )

    print("\n  # Get metrics with absolute time duration")
    print(
        "  linode-cli monitor-api get-metrics dbaas --entity-ids 123 "
        "--start-time 2024-10-10T00:00:01Z --end-time 2024-10-10T23:59:59Z "
        "--metrics cpu_usage:avg,memory_usage:sum"
    )

    print("\n  # Get metrics with filters")
    print(
        "  linode-cli monitor-api get-metrics dbaas --entity-ids 123 --duration 15 "
        "--duration-unit min --metrics cpu_usage:avg "
        "--filters 'node_type:in:primary,secondary'"
    )

    print("\n  # Get metrics with multiple filters")
    print(
        "  linode-cli monitor-api get-metrics dbaas --entity-ids 123 --duration 15 "
        "--duration-unit min --metrics cpu_usage:avg "
        "--filters 'node_type:in:primary,secondary;status:eq:active'"
    )

    print("\n  # Get metrics with granularity")
    print(
        "  linode-cli monitor-api get-metrics netloadbalancer --entity-ids 123 "
        "--duration 1 --duration-unit hour --metrics nlb_ingress_traffic:sum "
        "--granularity 10 --granularity-unit min"
    )

    print("\n  # Get metrics with entity region (required ObjectStorage)")
    print(
        "  linode-cli monitor-api get-metrics objectstorage --entity-region us-east-1 "
        "--duration 15 --duration-unit min --metrics obj_requests_num:sum"
    )

    print(
        "\n  # Get metrics with associated entity region "
        "(mandatory for cloud firewall service)"
    )
    print(
        "  linode-cli monitor-api get-metrics firewall --entity-region us-east-1 "
        "--associated-entity-region us-west-1 --duration 15 "
        "--duration-unit min --metrics fw_active_connections:sum"
    )


def get_metrics_parser():
    """
    Build argument parser for metrics plugin
    """
    parser = ArgumentParser(
        PLUGIN_BASE, add_help=False, formatter_class=SortingHelpFormatter
    )

    register_debug_arg(parser)

    # Command as first positional argument
    parser.add_argument(
        "command",
        nargs="?",
        help="Command to execute (get-metrics)",
    )

    # Service name as second positional argument
    parser.add_argument(
        "service",
        nargs="?",
        help="Service name (Dbaas, Nodebalancer, NetLoadBalancer, Linode, "
        "Firewall, ObjectStorage, Blockstorage, LKE)",
    )

    # Optional arguments for get-metrics functionality
    parser.add_argument(
        "--entity-ids",
        help="Comma-separated list of entity IDs "
        "(can be integers or strings depending on service type)",
        required=False,
    )

    parser.add_argument(
        "--entity-region",
        help="Region for entities (required for services like ObjectStorage)",
        required=False,
    )

    parser.add_argument(
        "--associated-entity-region",
        help="Associated region for entities (Required for cloud firewall service)",
        required=False,
    )

    # Time duration options - either relative or absolute
    parser.add_argument(
        "--duration",
        type=int,
        help="Relative time duration to look back (e.g., 15 for 15 minutes)",
    )
    parser.add_argument(
        "--duration-unit", help="Unit for relative duration: min, hr, day"
    )
    parser.add_argument(
        "--start-time",
        help="Absolute start time (ISO format: 2024-10-10T00:00:01Z)",
    )
    parser.add_argument(
        "--end-time",
        help="Absolute end time (ISO format: 2024-10-10T23:59:59Z)",
    )

    parser.add_argument(
        "--metrics",
        help="Comma-separated list of metrics with mandatory aggregate functions. "
        "Format: 'metric1:function1,metric2:function2' "
        "(e.g., 'cpu_usage:avg,memory_usage:sum')",
    )
    parser.add_argument(
        "--granularity",
        type=int,
        help="Time granularity for data points (optional)",
    )
    parser.add_argument(
        "--granularity-unit",
        help="Unit for granularity: min, hr, day (optional)",
    )
    parser.add_argument(
        "--filters",
        help="Optional filters in format 'dimension:operator:value'. "
        "Multiple filters separated by semicolons. "
        "Example: 'node_type:in:primary,secondary;status:eq:active'",
    )
    parser.add_argument(
        "--group_by",
        help="Comma-separated list of fields to group by (default: entity_id)",
    )

    return parser


def validate_arguments(parsed):
    """Validate required arguments"""
    if not parsed.metrics:
        print(
            "Missing required arguments for metrics retrieval:", file=sys.stderr
        )
        print("  --metrics: required", file=sys.stderr)
        return False

    # Validate time duration arguments
    has_relative = (
        parsed.duration is not None and parsed.duration_unit is not None
    )
    has_absolute = parsed.start_time is not None and parsed.end_time is not None

    if not has_relative and not has_absolute:
        print("Time duration required:", file=sys.stderr)
        print("  Either: --duration and --duration-unit", file=sys.stderr)
        print("  Or: --start-time and --end-time", file=sys.stderr)
        return False

    if has_relative and has_absolute:
        print(
            "Cannot specify both relative and absolute time duration",
            file=sys.stderr,
        )
        return False

    return True


def parse_entity_ids(entity_ids_str: Optional[str]) -> List:
    """Parse entity IDs from string"""
    entity_ids = []
    if entity_ids_str:
        for entity_id in entity_ids_str.split(","):
            entity_id = entity_id.strip()
            try:
                entity_ids.append(int(entity_id))
            except ValueError:
                entity_ids.append(entity_id)
    return entity_ids


def call(args, context=None):  # pylint: disable=unused-argument
    """The entrypoint for this plugin"""
    parser = get_metrics_parser()
    parsed, remaining_args = parser.parse_known_args(args)

    # Handle help cases
    if not parsed.command or parsed.command == "help" or "--help" in args:
        print_help(parser)
        sys.exit(ExitCodes.SUCCESS)

    # Validate command
    if parsed.command != "get-metrics":
        print(f"Unknown command: {parsed.command}", file=sys.stderr)
        print("Available commands: get-metrics", file=sys.stderr)
        print_help(parser)
        sys.exit(ExitCodes.REQUEST_FAILED)

    # Validate service is provided
    if not parsed.service:
        print("Service name is required", file=sys.stderr)
        print_help(parser)
        sys.exit(ExitCodes.REQUEST_FAILED)

    if remaining_args:
        print(f"Unknown arguments: {' '.join(remaining_args)}", file=sys.stderr)
        print_help(parser)
        sys.exit(ExitCodes.REQUEST_FAILED)

    # Validate arguments
    if not validate_arguments(parsed):
        print_help(parser)
        sys.exit(ExitCodes.REQUEST_FAILED)

    # Parse arguments
    entity_ids = parse_entity_ids(parsed.entity_ids)
    metrics = [x.strip() for x in parsed.metrics.split(",")]
    group_by = None
    if parsed.group_by:
        group_by = [x.strip() for x in parsed.group_by.split(",")]
    filters = None
    if parsed.filters:
        filters = [x.strip() for x in parsed.filters.split(";")]

    # Create config and call get_metrics
    config = MetricsConfig(
        service_name=parsed.service,
        entity_ids=entity_ids,
        duration=parsed.duration,
        duration_unit=parsed.duration_unit,
        start_time=parsed.start_time,
        end_time=parsed.end_time,
        metrics=metrics,
        granularity=parsed.granularity,
        granularity_unit=parsed.granularity_unit,
        filters=filters,
        group_by=group_by,
        entity_region=parsed.entity_region,
        associated_entity_region=parsed.associated_entity_region,
    )

    get_metrics(config)
