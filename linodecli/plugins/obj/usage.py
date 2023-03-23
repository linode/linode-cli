"""
Resources for usage checking commands.
"""
import sys
from argparse import ArgumentParser

from linodecli.plugins import inherit_plugin_args
from linodecli.plugins.obj.config import PLUGIN_BASE
from linodecli.plugins.obj.helpers import (
    _borderless_table,
    _denominate,
    _pad_to,
)

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass


def show_usage(get_client, args):
    """
    Shows space used by all buckets in this cluster, and total space
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " du"))

    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        nargs="?",
        help="Optional.  If given, only shows usage for that bucket. "
        "If omitted, shows usage for all buckets.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    if parsed.bucket:
        bucket_names = [parsed.bucket]
    else:
        try:
            bucket_names = [
                b["Name"] for b in client.list_buckets().get("Buckets", [])
            ]
        except ClientError as e:
            sys.exit(e)

    grand_total = 0
    for b in bucket_names:
        try:
            objects = client.list_objects_v2(Bucket=b).get("Contents", [])
        except ClientError as e:
            sys.exit(e)
        total = 0
        obj_count = 0

        for obj in objects:
            total += obj.get("Size", 0)
            obj_count += 1

        grand_total += total
        total = _denominate(total)

        tab = _borderless_table(
            [[_pad_to(total, length=7), f"{obj_count} objects", b]]
        )
        print(tab.table)

    if len(bucket_names) > 1:
        print("--------")
        print(f"{_denominate(grand_total)} Total")

    sys.exit(0)
