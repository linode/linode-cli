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

from rich import print as rprint
from rich.table import Table

from linodecli.cli import CLI
from linodecli.configuration import _do_get_request
from linodecli.configuration.helpers import _default_thing_input
from linodecli.helpers import expand_globs
from linodecli.plugins import PluginContext, inherit_plugin_args
from linodecli.plugins.obj.buckets import create_bucket, delete_bucket
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
    _convert_datetime,
    _denominate,
    _pad_to,
    _progress,
    restricted_int_arg_type,
)
from linodecli.plugins.obj.objects import (
    delete_object,
    get_object,
    upload_object,
)

try:
    import boto3
    from boto3.exceptions import S3UploadFailedError
    from boto3.s3.transfer import MB, TransferConfig
    from botocore.exceptions import ClientError

    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def list_objects_or_buckets(
    get_client, args
):  # pylint: disable=too-many-locals
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

        sys.exit(0)
    else:
        # list buckets
        buckets = client.list_buckets().get("Buckets", [])
        data = [
            [_convert_datetime(b.get("CreationDate")), b.get("Name")]
            for b in buckets
        ]

        tab = _borderless_table(data)
        rprint(tab)

        sys.exit(0)


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


def set_acl(get_client, args):
    """
    Modify Access Control List for a Bucket or Objects
    """
    parser = inherit_plugin_args(ArgumentParser(PLUGIN_BASE + " setacl"))

    parser.add_argument(
        "bucket", metavar="BUCKET", type=str, help="The bucket to modify."
    )
    parser.add_argument(
        "file",
        metavar="OBJECT",
        type=str,
        nargs="?",
        help="Optional.  The object to modify.  If omitted, modifies "
        "the ACLs for the entire bucket.",
    )
    parser.add_argument(
        "--acl-public",
        action="store_true",
        help="If given, makes the target publicly readable.",
    )
    parser.add_argument(
        "--acl-private",
        action="store_true",
        help="If given, makes the target private.",
    )

    parsed = parser.parse_args(args)
    client = get_client()

    # make sure the call is sane
    if parsed.acl_public and parsed.acl_private:
        print("You may not set the ACL to public and private in the same call")
        sys.exit(1)

    if not parsed.acl_public and not parsed.acl_private:
        print("You must choose an ACL to apply")
        sys.exit(1)
    acl = "public-read" if parsed.acl_public else "private"
    bucket = parsed.bucket

    key = parsed.file
    set_acl_options = {
        "Bucket": bucket,
        "ACL": acl,
    }
    if key:
        set_acl_options["Key"] = key
        set_acl_func = client.put_object_acl
    else:
        set_acl_func = client.put_bucket_acl

    try:
        set_acl_func(**set_acl_options)
    except ClientError as e:
        sys.exit(e)
    print("ACL updated")


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
        rprint(tab)

    if len(bucket_names) > 1:
        print("--------")
        print(f"{_denominate(grand_total)} Total")

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

    tab = Table(show_header=False)
    for row in command_help_map:
        tab.add_row(*row)
    rprint(tab)
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


def regenerate_s3_credentials(cli: CLI):
    """
    Force regenerate object storage access key and secret key.
    """
    print("Regenerating Object Storage keys..")
    _get_s3_creds(cli, force=True)
    print("Done.")
    print(
        "Warning: Your old Object Storage keys _were not_ automatically expired!  If you want "
        "to expire them, see `linode-cli object-storage keys-list` and "
        "`linode-cli object-storage keys-delete [KEYID]`."
    )


def call(
    args: List[str], context: PluginContext
):  # pylint: disable=too-many-branches,too-many-statements
    """
    This is called when the plugin is invoked
    """
    if not HAS_BOTO:
        # we can't do anything - ask for an install
        print(
            "This plugin requires the 'boto3' module.  Please install it by running "
            "'pip3 install boto3' or 'pip install boto3'"
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
        return context.client.config.plugin_get_value("cluster")

    def get_client():
        """
        Get the boto3 client based on the cluster, or ask to configure a
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
    Returns a boto3 client object that can be used to communicate with the Object
    Storage cluster.
    """
    client = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=cluster,
        endpoint_url=BASE_URL_TEMPLATE.format(cluster),
    )

    # set this for later use
    client.cluster = cluster

    return client


def _get_s3_creds(client: CLI, force: bool = False):
    """
    Retrieves stored s3 creds for the acting user from the config, or generates new
    creds using the client and stores them if none exist

    :param client: The client object from the invoking PluginContext
    :type client: linodecli.CLI
    :param force: If True, get new creds even if there are already creds stored.
                  This is used to rotate creds.
    :type force: bool

    :returns: The access key and secret key for this user
    :rtype: tuple(str, str)
    """
    access_key = client.config.plugin_get_value("access-key")
    secret_key = client.config.plugin_get_value("secret-key")

    if force or access_key is None:
        # this means there are no stored s3 creds for this user - set them up

        # but first - is there actually a config?  If we got this far, creds aren't
        # being provided by the environment, but if the CLI is running without a
        # config, we shouldn't generate new keys (or we'd end up doing so with each
        # request) - instead ask for them to be set up.
        if client.config.get_value("token") is None:
            print(
                "You are running the Linode CLI without a configuration file, but "
                "object storage keys were not configured.  "
                "Please set the following variables in your environment: "
                f"'{ENV_ACCESS_KEY_NAME}' and '{ENV_SECRET_KEY_NAME}'.  If you'd rather "
                "configure the CLI, unset the 'LINODE_CLI_TOKEN' environment "
                "variable and then run `linode-cli configure`."
            )
            sys.exit(1)

        # before we do anything, can they do object storage?
        status, resp = client.call_operation("account", "view")

        if status != 200:
            if status == 401:
                # special case - oauth token isn't allowed to do this
                print(NO_SCOPES_ERROR)
                sys.exit(4)
            if status == 403:
                # special case - restricted users can't use obj
                print(NO_ACCESS_ERROR)
                sys.exit(4)
            # something went wrong - give up
            print("Key generation failed!")
            sys.exit(4)

        # label caps at 50 characters - trim some stuff maybe
        # static characters in label account for 13 total
        # timestamp is 10 more
        # allow 13 characters both for username and hostname
        timestamp_part = str(time.time()).split(".", maxsplit=1)[0]
        truncated_user = getpass.getuser()[:13]
        truncated_hostname = socket.gethostname()[:13]

        creds_label = (
            f"linode-cli-{truncated_user}@{truncated_hostname}-{timestamp_part}"
        )

        if len(creds_label) > 50:
            # if this is somehow still too long, trim from the front
            creds_label = creds_label[50 - len(creds_label) :]

        status, resp = client.call_operation(
            "object-storage", "keys-create", ["--label", f"{creds_label}"]
        )

        if status != 200:
            if status == 401:
                # special case - oauth token isn't allowed to do this
                print(NO_SCOPES_ERROR)
                sys.exit(4)
            if status == 403:
                # special case - restricted users can't use obj
                print(NO_ACCESS_ERROR)
                sys.exit(4)
            # something went wrong - give up
            print("Key generation failed!")
            sys.exit(3)

        access_key = resp["access_key"]
        secret_key = resp["secret_key"]

        client.config.plugin_set_value("access-key", access_key)
        client.config.plugin_set_value("secret-key", secret_key)
        client.config.write_config()

    return access_key, secret_key


def _configure_plugin(client: CLI):
    """
    Configures a default cluster value.
    """
    clusters = [
        c["id"]
        for c in _do_get_request(  # pylint: disable=protected-access
            client.config.base_url,
            "/object-storage/clusters",
            token=client.config.get_value("token"),
        )["data"]
    ]

    cluster = _default_thing_input(  # pylint: disable=protected-access
        "Configure a default Cluster for operations.",
        clusters,
        "Default Cluster: ",
        "Please select a valid Cluster",
        optional=False,  # this is the only configuration right now
    )

    client.config.plugin_set_value("cluster", cluster)
    client.config.write_config()
