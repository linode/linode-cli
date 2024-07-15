"""
Various helper functions shared across multiple CLI components.
"""

import glob
import os
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

API_HOST_OVERRIDE = os.getenv("LINODE_CLI_API_HOST")
API_VERSION_OVERRIDE = os.getenv("LINODE_CLI_API_VERSION")
API_SCHEME_OVERRIDE = os.getenv("LINODE_CLI_API_SCHEME")

# A user-specified path to the CA file for use in API requests.
# This field defaults to True to enable default verification if
# no path is specified.
API_CA_PATH = os.getenv("LINODE_CLI_CA", None) or True


def handle_url_overrides(
    url: str,
    host: Optional[str] = None,
    version: Optional[str] = None,
    scheme: Optional[str] = None,
    override_path: bool = False,
):
    """
    Returns the URL with the API URL environment overrides applied.
    If override_path is True and the API version env var is specified,
    the URL path will be updated accordingly.
    """

    parsed_url = urlparse(url)

    overrides = {
        "netloc": API_HOST_OVERRIDE or host,
        "path": (API_VERSION_OVERRIDE or version) if override_path else None,
        "scheme": API_SCHEME_OVERRIDE or scheme,
    }

    # Apply overrides
    return parsed_url._replace(
        **{k: v for k, v in overrides.items() if v is not None}
    ).geturl()


def register_pagination_args_shared(parser: ArgumentParser):
    """
    Add pagination related arguments to the given
    ArgumentParser that may be shared across the CLI and plugins.
    """
    parser.add_argument(
        "--page",
        metavar="PAGE",
        default=1,
        type=int,
        help="For listing actions, specifies the page to request",
    )
    parser.add_argument(
        "--page-size",
        metavar="PAGESIZE",
        default=100,
        type=int,
        help="For listing actions, specifies the number of items per page, "
        "accepts any value between 25 and 500",
    )
    parser.add_argument(
        "--all-rows",
        action="store_true",
        help="Output all possible rows in the results with pagination",
    )


def register_args_shared(parser: ArgumentParser):
    """
    Adds certain arguments to the given ArgumentParser that may be shared across
    the CLI and plugins.
    This function is wrapped in linodecli.plugins.

    NOTE: This file is not located in arg_helpers.py to prevent a cyclic dependency.
    """

    parser.add_argument(
        "--as-user",
        metavar="USERNAME",
        type=str,
        help="The username to execute this command as.  This user must "
        "be configured.",
    )

    parser.add_argument(
        "--suppress-warnings",
        action="store_true",
        help="Suppress warnings that are intended for human users. "
        "This is useful for scripting the CLI's behavior.",
    )

    return parser


def register_debug_arg(parser: ArgumentParser):
    """
    Add the debug argument to the given
    ArgumentParser that may be shared across the CLI and plugins.
    """
    parser.add_argument(
        "--debug", action="store_true", help="Enable verbose HTTP debug output."
    )


def expand_globs(pattern: str):
    """
    Expand glob pattern (for example, '/some/path/*.txt')
    to be a list of path object.
    """
    results = glob.glob(pattern, recursive=True)
    if len(results) < 1:
        print(f"No file found matching pattern {pattern}")

    return [Path(x).resolve() for x in results]
