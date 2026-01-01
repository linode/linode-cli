"""
This plugin allows users to query metrics from the monitoring service for various services.

"""

import json
import os
import sys
from argparse import ArgumentParser
from typing import List, Optional

import requests
import urllib3

from linodecli.exit_codes import ExitCodes
from linodecli.help_formatter import SortingHelpFormatter
from linodecli.helpers import register_debug_arg

PLUGIN_BASE = "linode-cli get_metrics"

# API Configuration
API_BASE_URL = "https://monitor-api.linode.com/v2/monitor/services"


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
    url = f"{API_BASE_URL}/{service_name}/{endpoint}"

    headers = {
        "Authorization": f"Bearer {token or get_auth_token()}",
        "Authentication-type": "jwe",
        "Pragma": "akamai-x-get-extracted-values",
        "Content-Type": "application/json",
    }

    try:
        if method.upper() == "POST":
            response = requests.post(
                url, headers=headers, json=data, timeout=30, verify=False
            )
        else:
            response = requests.get(
                url, headers=headers, timeout=30, verify=False
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


def get_metrics(
    service_name: str,
    entity_ids: List,
    duration: Optional[int],
    duration_unit: Optional[str],
    start_time: Optional[str],
    end_time: Optional[str],
    metrics: List[str],
    granularity: Optional[int],
    granularity_unit: Optional[str],
    filters: Optional[List[str]] = None,
    group_by: Optional[List[str]] = None,
    entity_region: Optional[str] = None,
    associated_entity_region: Optional[str] = None,
    token: Optional[str] = None,
):
    """
    Get metrics for specified service entities
    """

    # Parse metrics with mandatory aggregate functions
    parsed_metrics = []
    for metric in metrics:
        if ":" in metric:
            metric_name, agg_func = metric.split(":", 1)
            parsed_metrics.append(
                {"aggregate_function": agg_func, "name": metric_name.strip()}
            )
        else:
            # No aggregate function specified - this is an error
            print(
                f"Aggregate function required for metric '{metric}'",
                file=sys.stderr,
            )
            print(
                f"Format: 'metric_name:function' where function is one of: {', '.join(AGGREGATE_FUNCTIONS)}",
                file=sys.stderr,
            )
            sys.exit(ExitCodes.REQUEST_FAILED)

    # Build request payload
    payload = {"metrics": parsed_metrics}
    if entity_ids:
        payload["entity_ids"] = entity_ids
    if group_by:
        payload["group_by"] = group_by
    if entity_region:
        payload["entity_region"] = entity_region
    if associated_entity_region:
        payload["associated_entity_region"] = associated_entity_region

    # Add time duration - either relative or absolute
    if start_time and end_time:
        payload["absolute_time_duration"] = {
            "start": start_time,
            "end": end_time,
        }
    elif duration is not None and duration_unit is not None:
        payload["relative_time_duration"] = {
            "unit": duration_unit,
            "value": duration,
        }
    else:
        print(
            "Either (--duration and --duration-unit) or (--start-time and --end-time) must be provided",
            file=sys.stderr,
        )
        sys.exit(ExitCodes.REQUEST_FAILED)

    # Add time_granularity only if both granularity and granularity_unit are provided
    if granularity is not None and granularity_unit is not None:
        payload["time_granularity"] = {
            "unit": granularity_unit,
            "value": granularity,
        }

    # Add filters if provided
    if filters:
        parsed_filters = []
        for filter_str in filters:
            parts = filter_str.split(
                ":", 2
            )  # Split into max 3 parts: dimension, operator, value
            if len(parts) != 3:
                print(
                    f"Invalid filter format: '{filter_str}'. Expected format: 'dimension:operator:value'",
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

    if entity_ids:
        print(f"Fetching metrics for {service_name} entities: {entity_ids}")
    else:
        print(f"Fetching metrics for {service_name} (all entities)")
    print(f"Request payload: {json.dumps(payload, indent=2)}")
    try:
        status, response = make_api_request(
            service_name, "metrics", "POST", payload, token
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
        "  linode-cli get_metrics dbaas --entity-ids 123 --duration 15 --duration-unit min --metrics cpu_usage:avg"
    )

    print("\n  # Get metrics for all entities (only allowed for objectstorage service)")
    print(
        "  linode-cli get_metrics objectstorage --duration 15 --duration-unit min --metrics obj_requests_num:avg --entity-region us-east-1"
    )

    print("\n  # Get metrics with absolute time duration")
    print(
        "  linode-cli get_metrics dbaas --entity-ids 123 --start-time 2024-10-10T00:00:01Z --end-time 2024-10-10T23:59:59Z --metrics cpu_usage:avg,memory_usage:sum"
    )

    print("\n  # Get metrics with filters")
    print(
        "  linode-cli get_metrics dbaas --entity-ids 123 --duration 15 --duration-unit min --metrics cpu_usage:avg --filters 'node_type:in:primary,secondary'"
    )

    print("\n  # Get metrics with multiple filters")
    print(
        "  linode-cli get_metrics dbaas --entity-ids 123 --duration 15 --duration-unit min --metrics cpu_usage:avg --filters 'node_type:in:primary,secondary;status:eq:active'"
    )

    print("\n  # Get metrics with granularity")
    print(
        "  linode-cli get_metrics netloadbalancer --entity-ids 123 --duration 1 --duration-unit hour --metrics nlb_ingress_traffic:sum --granularity 10 --granularity-unit min"
    )

    print("\n  # Get metrics with entity region (required ObjectStorage)")
    print(
        "  linode-cli get_metrics objectstorage --entity-region us-east-1 --duration 15 --duration-unit min --metrics obj_requests_num:sum"
    )

    print("\n  # Get metrics with associated entity region (mandatory for cloud firewall service)")
    print(
        "  linode-cli get_metrics firewall --entity-region us-east-1 --associated-entity-region us-west-1 --duration 15 --duration-unit min --metrics fw_active_connections:sum"
    )


def get_metrics_parser():
    """
    Build argument parser for metrics plugin
    """
    parser = ArgumentParser(
        PLUGIN_BASE, add_help=False, formatter_class=SortingHelpFormatter
    )

    register_debug_arg(parser)

    # Service name as positional argument
    parser.add_argument(
        "service",
        nargs="?",
        help="Service name (Dbaas, Nodebalancer, NetLoadBalancer, Linode, Firewall, ObjectStorage, Blockstorage,LKE)",
    )

    # Optional arguments for get-metrics functionality
    parser.add_argument(
        "--entity-ids",
        help="Comma-separated list of entity IDs (can be integers or strings depending on service type)",
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
        help="Comma-separated list of metrics with mandatory aggregate functions. Format: 'metric1:function1,metric2:function2' (e.g., 'cpu_usage:avg,memory_usage:sum')",
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
        help="Optional filters in format 'dimension:operator:value'. Multiple filters separated by semicolons. Example: 'node_type:in:primary,secondary;status:eq:active'",
    )
    parser.add_argument(
        "--group_by",
        help="Comma-separated list of fields to group by (default: entity_id)",
    )

    return parser


def call(args, context):
    """
    The entrypoint for this plugin
    """
    parser = get_metrics_parser()
    parsed, remaining_args = parser.parse_known_args(args)

    # Handle help cases
    if not parsed.service or parsed.service == "help" or "--help" in args:
        print_help(parser)
        sys.exit(ExitCodes.SUCCESS)

    if remaining_args:
        print(f"Unknown arguments: {' '.join(remaining_args)}", file=sys.stderr)
        print_help(parser)
        sys.exit(ExitCodes.REQUEST_FAILED)

    # Validate required arguments for get-metrics functionality
    if not parsed.metrics:
        print(
            "Missing required arguments for metrics retrieval:", file=sys.stderr
        )
        print("  --metrics: required", file=sys.stderr)
        print_help(parser)
        sys.exit(ExitCodes.REQUEST_FAILED)

    # Validate time duration arguments - either relative or absolute required
    has_relative = (
        parsed.duration is not None and parsed.duration_unit is not None
    )
    has_absolute = parsed.start_time is not None and parsed.end_time is not None

    if not has_relative and not has_absolute:
        print("Time duration required:", file=sys.stderr)
        print("  Either: --duration and --duration-unit", file=sys.stderr)
        print("  Or: --start-time and --end-time", file=sys.stderr)
        print_help(parser)
        sys.exit(ExitCodes.REQUEST_FAILED)

    if has_relative and has_absolute:
        print(
            "Cannot specify both relative and absolute time duration",
            file=sys.stderr,
        )
        sys.exit(ExitCodes.REQUEST_FAILED)

    # Parse entity IDs (can be integers or strings depending on service type)
    entity_ids = []
    if parsed.entity_ids:
        for entity_id in parsed.entity_ids.split(","):
            entity_id = entity_id.strip()
            # Try to convert to int first, if that fails keep as string
            try:
                entity_ids.append(int(entity_id))
            except ValueError:
                entity_ids.append(entity_id)

    # Parse metrics
    metrics = [x.strip() for x in parsed.metrics.split(",")]

    # Parse group_by if provided
    group_by = None
    if parsed.group_by:
        group_by = [x.strip() for x in parsed.group_by.split(",")]

    # Parse filters if provided
    filters = None
    if parsed.filters:
        filters = [x.strip() for x in parsed.filters.split(";")]

    get_metrics(
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
