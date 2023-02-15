"""
Various helper functions shared across multiple CLI components.
"""

import os
import re
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
