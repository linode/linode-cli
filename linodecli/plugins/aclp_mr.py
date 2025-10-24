#!/usr/bin/env python3
from argparse import ArgumentParser
from linodecli.help_formatter import SortingHelpFormatter
import requests
from linodecli.helpers import register_debug_arg
import json
import sys

PLUGIN_BASE = "linode-cli aclp_mr"
MANDATORY_HEADER = ["Authorization"]
MANDATORY_DATA = ["metrics","time_granularity"]

def get_metadata_parser():
    """
    Builds argparser for Metadata plug-in
    """
    parser = ArgumentParser(
        PLUGIN_BASE, add_help=False, formatter_class=SortingHelpFormatter, description="Python CLI to make HTTP GET requests to ACLP Metric Read Service"
    )

    register_debug_arg(parser)

    parser.add_argument("--url", "-u", required=True, help="URL to send GET request to")
    parser.add_argument(
        "--header", "-H",
        action="append",
        required=True,
        help="Add custom headers (format: Key:Value)",
        default=[]
    )

    parser.add_argument(
        "--cacert", "-c",
        type=str,
        help="Add ca certificate to validate server",
        default=False
    )

    parser.add_argument(
        "--data", "-d",
        type=json.loads, 
        required=True,
        help="payload for MR requests"
    )

    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=10, 
        help="Request timeout in seconds (default: 10)"
    )

    return parser

def header_parser(args):
    headers = {}
    print(args.header)
    for h in args.header:
        if ":" in h:
            key, value = h.split(":", 1)
            headers[key.strip()] = value.strip()

    
    return headers

def data_parser(args):
    return args.data

def call(args, context):
    """
    The entrypoint for this plugin
    """
    parser = get_metadata_parser()
    parsed, args = parser.parse_known_args(args)

    # parse headers
    headers = header_parser(parsed)
    data = data_parser(parsed)
    print(data)

    try:
        response = requests.post(parsed.url, headers=headers, json=data, timeout=parsed.timeout, verify=parsed.cacert)
        #for k, v in response.headers.items():
        #    print(f"  {k}: {v}")

        print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        sys.exit(1)

