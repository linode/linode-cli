# pylint: disable=too-many-lines
"""
CLI Plugin for handling OBJ
"""
import getpass
import os
import socket
import sys
import time
from argparse import ArgumentParser
from contextlib import suppress
from datetime import datetime
from math import ceil
from typing import List

from rich import print as rprint
from rich.table import Table

from linodecli.cli import CLI
from linodecli.configuration import _do_get_request
from linodecli.configuration.helpers import _default_text_input
from linodecli.exit_codes import ExitCodes
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
    _denominate,
    _pad_to,
)
from linodecli.plugins.obj.list import list_all_objects, list_objects_or_buckets
from linodecli.plugins.obj.objects import (
    delete_object,
    get_object,
    upload_object,
)
from linodecli.plugins.obj.website import (
    disable_static_site,
    enable_static_site,
    static_site_info,
)

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError

    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def generate_url(get_client, args, **kwargs):  # pylint: disable=unused-argument
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


def set_acl(get_client, args, **kwargs):  # pylint: disable=unused-argument
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
        print(
            "You may not set the ACL to public and private in the same call",
            file=sys.stderr,
        )
        sys.exit(ExitCodes.REQUEST_FAILED)

    if not parsed.acl_public and not parsed.acl_private:
        print("You must choose an ACL to apply", file=sys.stderr)
        sys.exit(ExitCodes.REQUEST_FAILED)
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
    except ClientError:
        sys.exit(ExitCodes.REQUEST_FAILED)
    print("ACL updated")


def show_usage(get_client, args, **kwargs):  # pylint: disable=unused-argument
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
        except ClientError:
            sys.exit(ExitCodes.REQUEST_FAILED)

    grand_total = 0
    for b in bucket_names:
        try:
            objects = client.list_objects_v2(Bucket=b).get("Contents", [])
        except ClientError:
            sys.exit(ExitCodes.REQUEST_FAILED)
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

    sys.exit(ExitCodes.SUCCESS)


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
    rprint("[bold cyan]Available commands: ")

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
            f"and {ENV_SECRET_KEY_NAME}, or neither",
            file=sys.stderr,
        )
        sys.exit(ExitCodes.REQUEST_FAILED)

    # not given on command line, so look them up
    if not access_key:
        access_key, secret_key = _get_s3_creds(cli)

    return access_key, secret_key


def regenerate_s3_credentials(cli: CLI, suppress_warnings=False):
    """
    Force regenerate object storage access key and secret key.
    """
    print("Regenerating Object Storage keys..")
    _get_s3_creds(cli, force=True)
    print("Done.")

    if not suppress_warnings:
        print(
            "WARNING: Your old Object Storage keys _were not_ automatically expired!  If you want "
            "to expire them, see `linode-cli object-storage keys-list` and "
            "`linode-cli object-storage keys-delete [KEYID]`.",
            file=sys.stderr,
        )


def call(
    args: List[str], context: PluginContext
):  # pylint: disable=too-many-branches,too-many-statements
    """
    This is called when the plugin is invoked
    """
    is_help = "--help" in args or "-h" in args

    if not HAS_BOTO:
        # we can't do anything - ask for an install
        print(
            "This plugin requires the 'boto3' module.  Please install it by running "
            "'pip3 install boto3' or 'pip install boto3'"
        )

        sys.exit(
            ExitCodes.REQUEST_FAILED
        )  # requirements not met - we can't go on

    parser = get_obj_args_parser()
    parsed, args = parser.parse_known_args(args)

    # don't mind --no-defaults if it's there; the top-level parser already took care of it
    with suppress(ValueError):
        args.remove("--no-defaults")

    if not parsed.command:
        print_help(parser)
        sys.exit(ExitCodes.SUCCESS)

    access_key = None
    secret_key = None

    # make a client, but only if we weren't printing help
    if not is_help:
        access_key, secret_key = get_credentials(context.client)

    cluster = parsed.cluster
    if context.client.defaults:
        cluster = cluster or context.client.config.plugin_get_value("cluster")

    def try_get_default_cluster():
        if not context.client.defaults:
            print("Error: cluster is required.", file=sys.stderr)
            sys.exit(ExitCodes.REQUEST_FAILED)

        print(
            "Error: No default cluster is configured.  Either configure the CLI "
            "or invoke with --cluster to specify a cluster.",
            file=sys.stderr,
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
            COMMAND_MAP[parsed.command](
                get_client, args, suppress_warnings=parsed.suppress_warnings
            )
        except ClientError as e:
            print(e, file=sys.stderr)
            sys.exit(ExitCodes.REQUEST_FAILED)
    elif parsed.command == "regenerate-keys":
        regenerate_s3_credentials(
            context.client, suppress_warnings=parsed.suppress_warnings
        )
    elif parsed.command == "configure":
        _configure_plugin(context.client)
    else:
        print(f"No command {parsed.command}", file=sys.stderr)
        sys.exit(ExitCodes.REQUEST_FAILED)


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
        config=Config(
            # This addresses an incompatibility between boto3 1.36.x and
            # some third-party S3-compatible storage platforms.
            # In the future we may want to consider manually computing the
            # CRC32 hash of a file before uploading it.
            #
            # See: https://github.com/boto/boto3/issues/4398#issuecomment-2619946229
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
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
                "variable and then run `linode-cli configure`.",
                file=sys.stderr,
            )
            sys.exit(ExitCodes.REQUEST_FAILED)

        # before we do anything, can they do object storage?
        status, resp = client.call_operation("account", "view")

        if status != 200:
            if status == 401:
                # special case - oauth token isn't allowed to do this
                print(NO_SCOPES_ERROR, file=sys.stderr)
                sys.exit(ExitCodes.REQUEST_FAILED)
            if status == 403:
                # special case - restricted users can't use obj
                print(NO_ACCESS_ERROR, file=sys.stderr)
                sys.exit(ExitCodes.REQUEST_FAILED)
            # something went wrong - give up
            print("Key generation failed!", file=sys.stderr)
            sys.exit(ExitCodes.REQUEST_FAILED)

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
                print(NO_SCOPES_ERROR, file=sys.stderr)
                sys.exit(ExitCodes.REQUEST_FAILED)
            if status == 403:
                # special case - restricted users can't use obj
                print(NO_ACCESS_ERROR, file=sys.stderr)
                sys.exit(ExitCodes.REQUEST_FAILED)
            # something went wrong - give up
            print("Key generation failed!", file=sys.stderr)
            sys.exit(ExitCodes.REQUEST_FAILED)

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

    cluster = _default_text_input(  # pylint: disable=protected-access
        "Default cluster for operations (e.g. `us-mia-1`)",
        optional=False,
    )

    if cluster:
        client.config.plugin_set_value("cluster", cluster)
    client.config.write_config()
