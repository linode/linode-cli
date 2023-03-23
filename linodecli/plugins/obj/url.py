"""
Resources for generating url command.
"""
from argparse import ArgumentParser
from datetime import datetime
from math import ceil

from linodecli.plugins import inherit_plugin_args
from linodecli.plugins.obj.config import PLUGIN_BASE


def generate_url(get_client, args):
    """
    Generates a URL to an object
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " signurl"))

    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        help="The bucket containing the object.",
    )
    parser.add_argument(
        "file", metavar="OBJECT", type=str, help="The object to sign a URL to."
    )
    parser.add_argument(
        "expiry",
        metavar="EXPIRY",
        type=str,
        help="When this link should expire.  Treated as an epoch "
        "time if a number. If starts with a '+' treated as "
        "an offset.",
    )

    # TODO:
    # Add docs for date format and unit for 'expiry' parameter.

    parsed = parser.parse_args(args)
    client = get_client()

    now = datetime.now()

    if parsed.expiry.startswith("+"):
        # this is an offset in seconds
        offset = int(parsed.expiry[1:])
    else:
        expiry = int(parsed.expiry)
        offset = expiry - ceil(now.timestamp())

    bucket = parsed.bucket
    key = parsed.file

    url = client.generate_presigned_url(
        ClientMethod="get_object",
        ExpiresIn=offset,
        Params={"Bucket": bucket, "Key": key},
    )

    print(url)
