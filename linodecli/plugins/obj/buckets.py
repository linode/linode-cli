"""
The bucket manipulation module of CLI Plugin for handling object storage
"""

import sys
from argparse import ArgumentParser

from linodecli.exit_codes import ExitCodes
from linodecli.plugins import inherit_plugin_args
from linodecli.plugins.obj.config import PLUGIN_BASE
from linodecli.plugins.obj.helpers import _delete_all_objects


def create_bucket(
    get_client, args, **kwargs
):  # pylint: disable=unused-argument
    """
    Creates a new bucket
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " mb"))

    parser.add_argument(
        "name",
        metavar="NAME",
        type=str,
        help="The name of the bucket to create.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    client.create_bucket(Bucket=parsed.name)

    print(f"Bucket {parsed.name} created")
    sys.exit(ExitCodes.SUCCESS)


def delete_bucket(
    get_client, args, **kwargs
):  # pylint: disable=unused-argument
    """
    Deletes a bucket
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " rb"))

    parser.add_argument(
        "name",
        metavar="NAME",
        type=str,
        help="The name of the bucket to remove.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="If given, force removal of non-empty buckets by deleting "
        "all objects in the bucket before deleting the bucket.  For "
        "large buckets, this may take a while.",
    )

    parsed = parser.parse_args(args)
    client = get_client()
    bucket_name = parsed.name

    if parsed.recursive:
        _delete_all_objects(client, bucket_name)

    client.delete_bucket(Bucket=bucket_name)
    print(f"Bucket {parsed.name} removed")

    sys.exit(ExitCodes.SUCCESS)
