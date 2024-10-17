"""
The module for list things in the object storage service.
"""

import sys
from argparse import ArgumentParser

from rich import print as rprint

from linodecli.exit_codes import ExitCodes
from linodecli.helpers import register_pagination_args_shared
from linodecli.plugins import inherit_plugin_args
from linodecli.plugins.obj.config import PLUGIN_BASE
from linodecli.plugins.obj.helpers import (
    _borderless_table,
    _convert_datetime,
    _pad_to,
    flip_to_page,
)

TRUNCATED_MSG = (
    "Notice: Not all results were shown. If your would "
    "like to get more results, you can add the '--all-row' "
    "flag to the command or use the built-in pagination flags."
)


def list_objects_or_buckets(
    get_client, args, **kwargs
):  # pylint: disable=too-many-locals,unused-argument,too-many-branches
    """
    Lists buckets or objects
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " ls"))
    register_pagination_args_shared(parser)

    parser.add_argument(
        "bucket",
        metavar="NAME",
        type=str,
        nargs="?",
        help=(
            "Optional.  If not given, lists all buckets.  If given, "
            "lists the contents of the given bucket.  May contain a "
            "/ followed by a directory path to show the contents of "
            "a directory within the named bucket."
        ),
    )

    parsed = parser.parse_args(args)
    client = get_client()

    if parsed.bucket:
        # list objects
        if "/" in parsed.bucket:
            bucket_name, prefix = parsed.bucket.split("/", 1)
            if not prefix.endswith("/"):
                prefix += "/"
        else:
            bucket_name = parsed.bucket
            prefix = ""

        data = []
        objects = []
        sub_directories = []
        pages = client.get_paginator("list_objects_v2").paginate(
            Prefix=prefix,
            Bucket=bucket_name,
            Delimiter="/",
            PaginationConfig={"PageSize": parsed.page_size},
        )
        try:
            if parsed.all_rows:
                results = pages
            else:
                page = flip_to_page(pages, parsed.page)
                if page.get("IsTruncated", False):
                    print(TRUNCATED_MSG)

                results = [page]
        except client.exceptions.NoSuchBucket:
            print("No bucket named " + bucket_name, file=sys.stderr)
            sys.exit(ExitCodes.REQUEST_FAILED)

        for item in results:
            objects.extend(item.get("Contents", []))
            sub_directories.extend(item.get("CommonPrefixes", []))

        for d in sub_directories:
            data.append((" " * 16, "DIR", d.get("Prefix")))
        for obj in objects:
            key = obj.get("Key")

            # This is to remove the dir itself from the results
            # when the the files list inside a directory (prefix) are desired.
            if key == prefix:
                continue

            data.append(
                (
                    _convert_datetime(obj.get("LastModified")),
                    obj.get("Size"),
                    key,
                )
            )

        if data:
            tab = _borderless_table(data)
            rprint(tab)

        sys.exit(ExitCodes.SUCCESS)
    else:
        # list buckets
        buckets = client.list_buckets().get("Buckets", [])
        data = [
            [_convert_datetime(b.get("CreationDate")), b.get("Name")]
            for b in buckets
        ]

        tab = _borderless_table(data)
        rprint(tab)

        sys.exit(ExitCodes.SUCCESS)


def list_all_objects(
    get_client, args, **kwargs
):  # pylint: disable=unused-argument
    """
    Lists all objects in all buckets
    """
    # this is for printing help when --help is in the args
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " la"))
    register_pagination_args_shared(parser)

    parsed = parser.parse_args(args)

    client = get_client()

    buckets = [b["Name"] for b in client.list_buckets().get("Buckets", [])]

    for b in buckets:
        print()
        objects = []
        pages = client.get_paginator("list_objects_v2").paginate(
            Bucket=b, PaginationConfig={"PageSize": parsed.page_size}
        )
        if parsed.all_rows:
            results = pages
        else:
            page = flip_to_page(pages, parsed.page)
            if page.get("IsTruncated", False):
                print(TRUNCATED_MSG)

            results = [page]

        for page in results:
            objects.extend(page.get("Contents", []))

        for obj in objects:
            size = obj.get("Size", 0)

            print(
                f"{_convert_datetime(obj['LastModified'])} "
                f"{_pad_to(size, 9, right_align=True)}   "
                f"{b}/{obj['Key']}"
            )

    sys.exit(ExitCodes.SUCCESS)
