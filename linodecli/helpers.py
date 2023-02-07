import os
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
        'netloc': API_HOST_OVERRIDE,
        'path': API_VERSION_OVERRIDE,
        'scheme': API_SCHEME_OVERRIDE
    }

    # Apply overrides
    return parsed_url._replace(**{k: v for k, v in overrides.items() if v is not None}).geturl()
