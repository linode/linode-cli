# pylint: disable=too-many-lines
"""
CLI Plugin for handling OBJ
"""
import getpass
import glob
import math
import os
import platform
import socket
import sys
import time
from argparse import ArgumentParser
from contextlib import suppress
from datetime import datetime
from math import ceil
from pathlib import Path
from typing import List

from terminaltables import SingleTable

from linodecli.cli import CLI
from linodecli.configuration import _do_get_request
from linodecli.configuration.helpers import _default_thing_input
from linodecli.helpers import expand_globs
from linodecli.plugins import PluginContext, inherit_plugin_args
from linodecli.plugins.obj.acl import set_acl
from linodecli.plugins.obj.config import (
    BASE_URL_TEMPLATE,
    BASE_WEBSITE_TEMPLATE,
    DATE_FORMAT,
    ENV_ACCESS_KEY_NAME,
    ENV_SECRET_KEY_NAME,
    INCOMING_DATE_FORMAT,
    MULTIPART_UPLOAD_CHUNK_SIZE_DEFAULT,
    NO_ACCESS_ERROR,
    NO_SCOPES_ERROR,
    PLUGIN_BASE,
    PROGRESS_BAR_WIDTH,
    UPLOAD_MAX_FILE_SIZE,
)
from linodecli.plugins.obj.helpers import (
    ProgressPercentage,
    _borderless_table,
    _configure_plugin,
    _convert_datetime,
    _denominate,
    _get_s3_creds,
    _pad_to,
    _progress,
    bucket_accessible,
    object_accessible,
    regenerate_s3_credentials,
    restricted_int_arg_type,
)
from linodecli.plugins.obj.url import generate_url
from linodecli.plugins.obj.usage import show_usage

try:
    import boto3
    from boto3.exceptions import S3UploadFailedError
    from boto3.s3.transfer import MB, TransferConfig
    from boto.exception import BotoClientError, S3CreateError, S3ResponseError
    from boto.s3.prefix import Prefix
    from botocore.exceptions import ClientError

    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


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


def create_bucket(get_client, args):
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
    sys.exit(0)


def delete_bucket(get_client, args):
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

    if parsed.recursive:
        try:
            bucket = client.get_bucket(parsed.name)
        except S3ResponseError:
            print("No bucket named " + parsed.name)
            sys.exit(2)

        for c in bucket.list():
            print(f"delete: {parsed.name} {c.key}")
            bucket.delete_key(c)
    bucket_name = parsed.name
    try:
        client.delete_bucket(Bucket=bucket_name)
    except client.exceptions.NoSuchBucket:
        print("No bucket named " + bucket_name)
        sys.exit(2)
    print("Bucket {parsed.name} removed")

    sys.exit(0)


def upload_object(get_client, args):  # pylint: disable=too-many-locals
    """
    Uploads an object to object storage
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " put"))

    parser.add_argument(
        "file", metavar="FILE", type=str, nargs="+", help="The files to upload."
    )
    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        help="The bucket to put a file in.",
    )
    parser.add_argument(
        "--acl-public",
        action="store_true",
        help="If set, the new object can be downloaded without "
        "authentication.",
    )
    parser.add_argument(
        "--chunk-size",
        type=restricted_int_arg_type(5120),
        default=MULTIPART_UPLOAD_CHUNK_SIZE_DEFAULT,
        help="The size of file chunks when uploading large files, in MB.",
    )

    # TODO:
    # 1. Allow user specified key (filename on cloud)
    # 2. handle exceptions
    # 3. test windows globs
    # 4. As below:
    # parser.add_argument('--recursive', action='store_true',
    #                    help="If set, upload directories recursively.")

    parsed = parser.parse_args(args)
    client = get_client()

    to_upload = []
    # to_multipart_upload = []
    files = list(parsed.file)
    for c in files:
        file_path = Path(c).resolve()

        # Windows doesn't natively expand globs, so we should implement it here
        if platform.system() == "Windows" and "*" in file_path:
            results = expand_globs(file_path)
            files.extend(results)
            continue

        if not file_path.is_file():
            print(f"No file {file_path}")
            sys.exit(5)

        to_upload.append((file_path.name, file_path))

    policy = "public-read" if parsed.acl_public else None
    chunk_size = 1024 * 1024 * parsed.chunk_size

    upload_options = {
        "Bucket": parsed.bucket,
        "Config": TransferConfig(multipart_chunksize=chunk_size * MB),
        "Callback": ProgressPercentage(
            file_path.stat().st_size, PROGRESS_BAR_WIDTH
        ),
    }

    if policy:
        upload_options["ExtraArgs"] = {"ACL": policy}

    for filename, file_path in to_upload:
        print(f"Uploading {filename}:")
        upload_options["Filename"] = str(file_path.resolve())
        upload_options["Key"] = filename
        try:
            client.upload_file(**upload_options)
        except S3UploadFailedError as e:
            sys.exit(e)

    print("Done.")


def get_object(get_client, args):
    """
    Retrieves an uploaded object and writes it to a file
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " get"))

    parser.add_argument(
        "bucket", metavar="BUCKET", type=str, help="The bucket the file is in."
    )
    parser.add_argument(
        "file", metavar="OBJECT", type=str, help="The object to retrieve."
    )
    parser.add_argument(
        "destination",
        metavar="LOCAL_FILE",
        type=str,
        nargs="?",
        help="The destination file. If omitted, uses the object "
        "name and saves to the current directory.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    # find destination file
    destination = parsed.destination

    if destination is None:
        destination = parsed.file

    destination = Path(destination).resolve()

    # download the file
    bucket = parsed.bucket
    key = parsed.file

    response = client.head_object(
        Bucket=bucket,
        Key=key,
    )

    client.download_file(
        Bucket=bucket,
        Key=key,
        Filename=str(destination),
        Callback=ProgressPercentage(
            response.get("ContentLength", 0), PROGRESS_BAR_WIDTH
        ),
    )

    print("Done.")


def delete_object(get_client, args):
    """
    Removes a file from a bucket
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " del"))

    parser.add_argument(
        "bucket", metavar="BUCKET", type=str, help="The bucket to delete from."
    )
    parser.add_argument(
        "file", metavar="OBJECT", type=str, help="The object to remove."
    )

    parsed = parser.parse_args(args)
    client = get_client()
    bucket = parsed.bucket
    key = parsed.file

    client.delete_object(
        Bucket=bucket,
        Key=key,
    )

    print(f"{parsed.file} removed from {parsed.bucket}")


def enable_static_site(get_client, args):
    """
    Turns a bucket into a static website
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " ws-create"))

    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        help="The bucket to turn into a static site",
    )
    parser.add_argument(
        "--ws-index",
        metavar="INDEX",
        required=True,
        type=str,
        help="The file to serve as the index of the website",
    )
    parser.add_argument(
        "--ws-error",
        metavar="ERROR",
        type=str,
        help="The file to serve as the error page of the website",
    )

    parsed = parser.parse_args(args)
    client = get_client()
    bucket = parsed.bucket

    # make the site
    print(f"Setting bucket {bucket} access control to be 'public-read'")

    client.put_bucket_acl(
        Bucket=bucket,
        ACL="public-read",
    )

    index_page = parsed.ws_index

    ws_config = {"IndexDocument": {"Suffix": index_page}}
    if parsed.ws_error:
        ws_config["ErrorDocument"] = {"Key": parsed.ws_error}

    client.put_bucket_website(
        Bucket=bucket,
        WebsiteConfiguration=ws_config,
    )

    print(
        "Static site now available at "
        f"{BASE_WEBSITE_TEMPLATE.format(cluster=client.cluster, bucket=bucket)}"
        "\nIf you still can't access the website, please check the "
        "Access Control List setting of the website related objects (files) "
        "in your bucket."
    )


def static_site_info(get_client, args):
    """
    Returns info about a configured static site
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " ws-info"))

    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        help="The bucket to return static site information on.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    bucket = parsed.bucket

    response = client.get_bucket_website(Bucket=bucket)

    index = response.get("IndexDocument", {}).get("Suffix", "Not Configured")
    error = response.get("ErrorDocument", {}).get("Key", "Not Configured")

    endpoint = BASE_WEBSITE_TEMPLATE.format(
        cluster=client.cluster, bucket=bucket
    )

    print(f"Bucket {bucket}: Website configuration")
    print(f"Website endpoint: {endpoint}")
    print(f"Index document: {index}")
    print(f"Error document: {error}")


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


def disable_static_site(get_client, args):
    """
    Disables static site for a bucket
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " du"))

    parser.add_argument(
        "bucket",
        metavar="BUCKET",
        type=str,
        nargs="?",
        help="The bucket to disable static site for.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    bucket = parsed.bucket

    client.delete_bucket_website(Bucket=bucket)

    print(f"Website configuration deleted for {parsed.bucket}")


COMMAND_MAP = {
    "mb": create_bucket,
    "rb": delete_bucket,
    "ls": list_objects_or_buckets,
    "la": list_all_objects,
    "du": show_usage,
    "put": upload_object,
    "get": get_object,
    "rm": delete_object,
    "del": delete_object,
    #'sync': sync_dir, TODO - syncs a directory
    "signurl": generate_url,
    "setacl": set_acl,
    "ws-create": enable_static_site,
    "ws-info": static_site_info,
    "ws-delete": disable_static_site,
    #'info': get_info,
}


def print_help(parser: ArgumentParser):
    """
    Print out the help info to the standard output.
    """
    parser.print_help()

    # additional help
    print()
    print("Available commands: ")

    command_help_map = [
        [name, func.__doc__.strip()]
        for name, func in sorted(COMMAND_MAP.items())
    ]

    tab = SingleTable(command_help_map)
    tab.inner_heading_row_border = False
    print(tab.table)
    print()
    print(
        "Additionally, you can regenerate your Object Storage keys using the "
        "'regenerate-keys' command or configure defaults for the plugin using "
        "the 'configure' command."
    )
    print()
    print("See --help for individual commands for more information")


def get_obj_args_parser():
    """
    Initialize and return the argument parser for the obj plug-in.
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE, add_help=False))

    parser.add_argument(
        "command",
        metavar="COMMAND",
        nargs="?",
        type=str,
        help="The command to execute in object storage",
    )
    parser.add_argument(
        "--cluster",
        metavar="CLUSTER",
        type=str,
        help="The cluster to use for the operation",
    )

    return parser


def get_credentials(cli: CLI):
    """
    Get access_key and secret_key of the object storage.
    """
    access_key, secret_key = (
        os.getenv(ENV_ACCESS_KEY_NAME, None),
        os.getenv(ENV_SECRET_KEY_NAME, None),
    )
    if bool(access_key) != bool(secret_key):
        print(
            f"You must set both {ENV_ACCESS_KEY_NAME} "
            f"and {ENV_SECRET_KEY_NAME}, or neither"
        )
        sys.exit(1)

    # not given on command line, so look them up
    if not access_key:
        access_key, secret_key = _get_s3_creds(cli)

    return access_key, secret_key


def call(
    args: List[str], context: PluginContext
):  # pylint: disable=too-many-branches,too-many-statements
    """
    This is called when the plugin is invoked
    """
    if not HAS_BOTO:
        # we can't do anything - ask for an install
        print(
            "This plugin requires the 'boto' module.  Please install it by running "
            "'pip3 install boto' or 'pip install boto'"
        )

        sys.exit(2)  # requirements not met - we can't go on

    parser = get_obj_args_parser()
    parsed, args = parser.parse_known_args(args)

    # don't mind --no-defaults if it's there; the top-level parser already took care of it
    with suppress(ValueError):
        args.remove("--no-defaults")

    if not parsed.command:
        print_help(parser)
        sys.exit(0)

    access_key = None
    secret_key = None

    # make a client, but only if we weren't printing help
    if not "--help" in args:
        access_key, secret_key = get_credentials(context.client)

    cluster = parsed.cluster
    if context.client.defaults:
        cluster = cluster or context.client.config.plugin_get_value("cluster")

    def try_get_default_cluster():
        if not context.client.defaults:
            print("Error: cluster is required.")
            sys.exit(1)

        print(
            "Error: No default cluster is configured.  Either configure the CLI "
            "or invoke with --cluster to specify a cluster."
        )
        _configure_plugin(context.client)
        current_cluster = context.client.config.plugin_get_value("cluster")

    def get_client():
        """
        Get the boto client based on the cluster, or ask to configure a
        default cluster if one is not specified. This is in a method so
        command methods can do this work AFTER displaying help,
        that way help can be shown without specifying a cluster
        or having a valid OBJ key.
        """
        current_cluster = cluster
        if current_cluster is None:
            current_cluster = try_get_default_cluster()

        return _get_boto_client(current_cluster, access_key, secret_key)

    if parsed.command in COMMAND_MAP:
        try:
            COMMAND_MAP[parsed.command](get_client, args)
        except ClientError as e:
            sys.exit(f"Error: {e}")
    elif parsed.command == "regenerate-keys":
        regenerate_s3_credentials(context.client)
    elif parsed.command == "configure":
        _configure_plugin(context.client)
    else:
        print(f"No command {parsed.command}")
        sys.exit(1)


def _get_boto_client(cluster, access_key, secret_key):
    """
    Returns a boto client object that can be used to communicate with the Object
    Storage cluster.
    """
    client = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=cluster,
        endpoint_url=BASE_URL_TEMPLATE.format(cluster),
    )
    client.cluster = cluster
    # print(s3_client, type(s3_client))
    # boto3_bucket = s3.Bucket('mybucket')
    # client = boto.connect_s3(
    #     aws_access_key_id=access_key,
    #     aws_secret_access_key=secret_key,
    #     host=BASE_URL_TEMPLATE.format(cluster),
    #     calling_format=OrdinaryCallingFormat(),
    # )

    # # set this for later use
    # client.cluster = cluster
    # s3_client.get_buck
    return client
