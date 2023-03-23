"""
Various helper functions shared across multiple CLI components.
"""

import glob
import os
import re
from pathlib import Path
from urllib.parse import urlparse

API_HOST_OVERRIDE = os.getenv("LINODE_CLI_API_HOST")
API_VERSION_OVERRIDE = os.getenv("LINODE_CLI_API_VERSION")
API_SCHEME_OVERRIDE = os.getenv("LINODE_CLI_API_SCHEME")


def handle_url_overrides(url):
    """
    Returns the URL with the API URL environment overrides applied.
    """

    parsed_url = urlparse(url)

    overrides = {
        "netloc": API_HOST_OVERRIDE,
        "path": API_VERSION_OVERRIDE,
        "scheme": API_SCHEME_OVERRIDE,
    }

    # Apply overrides
    return parsed_url._replace(
        **{k: v for k, v in overrides.items() if v is not None}
    ).geturl()


def filter_markdown_links(text):
    """
    Returns the given text with Markdown links converted to human-readable links.
    """

    result = text

    # Find all Markdown links
    r = re.compile(r"\[(?P<text>.*?)]\((?P<link>.*?)\)")

    for match in r.finditer(text):
        url = match.group("link")

        # Expand the URL if necessary
        if url.startswith("/"):
            url = f"https://linode.com{url}"

        # Replace with more readable text
        result = result.replace(match.group(), f"{match.group('text')} ({url})")

    return result


def register_args_shared(parser):
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

    return parser


def expand_globs(pattern: str):
    """
    Expand glob pattern (for example, '/some/path/*.txt')
    to be a list of path object.
    """
    results = glob.glob(pattern, recursive=True)
    if len(results) < 1:
        print(f"No file found matching pattern {pattern}")

    return [Path(x).resolve() for x in results]
