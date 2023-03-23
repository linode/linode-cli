import sys
from argparse import ArgumentParser

from linodecli.plugins import inherit_plugin_args
from linodecli.plugins.obj.config import PLUGIN_BASE
from linodecli.plugins.obj.helpers import (
    _borderless_table,
    _convert_datetime,
    _pad_to,
)


def list_objects_or_buckets(get_client, args):
    """
    Lists buckets or objects
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " ls"))

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
        try:
            response = client.list_objects_v2(
                Prefix=prefix, Bucket=bucket_name, Delimiter="/"
            )
        except client.exceptions.NoSuchBucket:
            print("No bucket named " + bucket_name)
            sys.exit(2)

        objects = response.get("Contents", [])
        sub_directories = response.get("CommonPrefixes", [])

        for d in sub_directories:
            data.append((" " * 16, "DIR", d.get("Prefix")))
        for obj in objects:
            key = obj.get("Key")

            # This is to remove the dir itself from the results
            # when the the files list inside a dir is desired.
            if key == prefix:
                continue

            data.append((obj.get("LastModified"), obj.get("Size"), key))

        if data:
            tab = _borderless_table(data)
            print(tab.table)

        sys.exit(0)
    else:
        # list buckets
        buckets = client.list_buckets().get("Buckets", [])
        data = [[b.get("CreationDate"), b.get("Name")] for b in buckets]

        tab = _borderless_table(data)
        print(tab.table)

        sys.exit(0)


def list_all_objects(get_client, args):
    """
    Lists all objects in all buckets
    """
    # this is for printing help when --help is in the args
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " la"))

    parser.parse_args(args)

    client = get_client()

    # all buckets
    buckets = [b["Name"] for b in client.list_buckets().get("Buckets", [])]

    for b in buckets:
        print()
        objects = client.list_objects_v2(Bucket=b).get("Contents", [])

        for obj in objects:
            size = obj.get("Size", 0)

            print(
                f"{_convert_datetime(obj['LastModified'])} "
                f"{_pad_to(size, 9, right_align=True)}   "
                f"{b}/{obj['Key']}"
            )

    sys.exit(0)
