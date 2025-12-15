# pylint: disable=too-many-lines
"""
CLI Plugin for handling OBJ
"""
import getpass
import os
import re
import socket
import sys
import time
from argparse import ArgumentParser
from contextlib import suppress
from datetime import datetime
from math import ceil
from typing import List, Optional

from pytimeparse import parse as parse_time
from rich import print as rprint
from rich.table import Table

from linodecli.cli import CLI
from linodecli.configuration.helpers import _default_text_input
from linodecli.exit_codes import ExitCodes
from linodecli.help_formatter import SortingHelpFormatter
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


CLUSTER_KEY = "cluster"
KEY_CLEANUP_ENABLED_KEY = "key-cleanup-enabled"
KEY_LIFESPAN_KEY = "key-lifespan"
KEY_ROTATION_PERIOD_KEY = "key-rotation-period"
KEY_CLEANUP_BATCH_SIZE_KEY = "key-cleanup-batch-size"
LAST_KEY_CLEANUP_TIMESTAMP_KEY = "last-key-cleanup-timestamp"
ACCESS_KEY_KEY = "access-key"
SECRET_KEY_KEY = "secret-key"
TOKEN_KEY = "token"


def generate_url(get_client, args, **kwargs):  # pylint: disable=unused-argument
    """
    Generates a URL to an object
    """
    parser = inherit_plugin_args(
        ArgumentParser(
            PLUGIN_BASE + " signurl", formatter_class=SortingHelpFormatter
        )
    )

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
    parser = inherit_plugin_args(
        ArgumentParser(
            PLUGIN_BASE + " setacl", formatter_class=SortingHelpFormatter
        )
    )

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
    except ClientError as e:
        print(e, file=sys.stderr)
        sys.exit(ExitCodes.REQUEST_FAILED)
    print("ACL updated")


def show_usage(get_client, args, **kwargs):  # pylint: disable=unused-argument
    """
    Shows space used by all buckets in this cluster, and total space
    """
    parser = inherit_plugin_args(
        ArgumentParser(
            PLUGIN_BASE + " du", formatter_class=SortingHelpFormatter
        )
    )

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
            print(e, file=sys.stderr)
            sys.exit(ExitCodes.REQUEST_FAILED)

    grand_total = 0
    for b in bucket_names:
        try:
            objects = client.list_objects_v2(Bucket=b).get("Contents", [])
        except ClientError as e:
            print(e, file=sys.stderr)
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
    parser = inherit_plugin_args(
        ArgumentParser(
            PLUGIN_BASE, add_help=False, formatter_class=SortingHelpFormatter
        )
    )

    parser.add_argument(
        "command",
        metavar="COMMAND",
        nargs="?",
        type=str,
        help="The command to execute in object storage.",
    )
    parser.add_argument(
        "--cluster",
        metavar="CLUSTER",
        type=str,
        help="The cluster to use for the operation.",
    )
    parser.add_argument(
        "--force-key-cleanup",
        action="store_true",
        help="Performs cleanup of old linode-cli generated Object Storage keys"
        " before executing the Object Storage command. It overrides"
        " the --perform-key-cleanup option.",
    )
    parser.add_argument(
        "--key-cleanup-enabled",
        choices=["yes", "no"],
        help="If set to 'yes', performs cleanup of old linode-cli generated Object Storage"
        " keys before executing the Object Storage command. Cleanup occurs"
        " at most once every 24 hours.",
    )
    parser.add_argument(
        "--key-lifespan",
        type=str,
        help="Specifies the lifespan of linode-cli generated Object Storage keys"
        " (e.g. 30d for 30 days). Used only during key cleanup.",
    )
    parser.add_argument(
        "--key-rotation-period",
        type=str,
        help="Specifies the period after which the linode-cli generated Object Storage"
        " key must be rotated (e.g. 10d for 10 days). Used only during key cleanup.",
    )
    parser.add_argument(
        "--key-cleanup-batch-size",
        type=int,
        help="Number of old linode-cli generated Object Storage keys to clean up at once.",
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
            "'pip3 install boto3' or 'pip install boto3'",
            file=sys.stderr,
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

    # make a client and clean-up keys, but only if we weren't printing help
    if not is_help:
        _cleanup_keys(context.client, parsed)
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
    access_key = client.config.plugin_get_value(ACCESS_KEY_KEY)
    secret_key = client.config.plugin_get_value(SECRET_KEY_KEY)

    if force or access_key is None:
        # this means there are no stored s3 creds for this user - set them up

        # but first - is there actually a config?  If we got this far, creds aren't
        # being provided by the environment, but if the CLI is running without a
        # config, we shouldn't generate new keys (or we'd end up doing so with each
        # request) - instead ask for them to be set up.
        if client.config.get_value(TOKEN_KEY) is None:
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

        client.config.plugin_set_value(ACCESS_KEY_KEY, access_key)
        client.config.plugin_set_value(SECRET_KEY_KEY, secret_key)
        client.config.write_config()

    return access_key, secret_key


def _configure_plugin(client: CLI):
    """
    Configures Object Storage plugin.
    """
    cluster = _default_text_input(  # pylint: disable=protected-access
        "Default cluster for operations (e.g. `us-mia-1`)",
        optional=False,
    )

    if cluster:
        client.config.plugin_set_value(CLUSTER_KEY, cluster)

    client.config.write_config()


def _cleanup_keys(client: CLI, options) -> None:
    """
    Cleans up stale linode-cli generated object storage keys.
    """

    try:
        current_timestamp = int(time.time())
        if not _should_perform_key_cleanup(client, options, current_timestamp):
            return

        cleanup_message = (
            "Cleaning up old linode-cli generated Object Storage keys."
        )
        if not options.force_key_cleanup and not options.key_cleanup_enabled:
            cleanup_message += (
                " To disable this, use the '--key-cleanup-enabled no' option."
            )
        print(cleanup_message, file=sys.stderr)

        status, keys = client.call_operation("object-storage", "keys-list")
        if status != 200:
            print(
                "Failed to list object storage keys for cleanup",
                file=sys.stderr,
            )
            return

        key_lifespan = _get_key_lifespan(client, options)
        key_rotation_period = _get_key_rotation_period(client, options)
        cleanup_batch_size = _get_cleanup_batch_size(client, options)

        linode_cli_keys = _get_linode_cli_keys(
            keys["data"], key_lifespan, key_rotation_period, current_timestamp
        )

        _rotate_current_key_if_needed(client, linode_cli_keys)
        _delete_stale_keys(client, linode_cli_keys, cleanup_batch_size)

        client.config.plugin_set_value(
            LAST_KEY_CLEANUP_TIMESTAMP_KEY, str(current_timestamp)
        )
        client.config.write_config()

    except Exception as e:
        print(
            f"Unable to clean up stale linode-cli Object Storage keys: {e}",
            file=sys.stderr,
        )


def _should_perform_key_cleanup(
    client: CLI, options, current_timestamp
) -> bool:
    if options.force_key_cleanup:
        return True
    if not _is_key_cleanup_enabled(client, options):
        return False

    last_cleanup = client.config.plugin_get_value(
        LAST_KEY_CLEANUP_TIMESTAMP_KEY
    )

    # if we did a cleanup in the last 24 hours, skip it this time
    return (
        last_cleanup is None
        or int(last_cleanup) <= current_timestamp - 24 * 60 * 60
    )


def _is_key_cleanup_enabled(client, options) -> bool:
    if options.key_cleanup_enabled in ["yes", "no"]:
        return options.key_cleanup_enabled == "yes"
    return client.config.plugin_get_value(KEY_CLEANUP_ENABLED_KEY, True, bool)


def _get_key_lifespan(client, options) -> str:
    return options.key_lifespan or client.config.plugin_get_value(
        KEY_LIFESPAN_KEY, "30d"
    )


def _get_key_rotation_period(client, options) -> str:
    return options.key_rotation_period or client.config.plugin_get_value(
        KEY_ROTATION_PERIOD_KEY, "10d"
    )


def _get_cleanup_batch_size(client, options) -> int:
    return options.key_cleanup_batch_size or client.config.plugin_get_value(
        KEY_CLEANUP_BATCH_SIZE_KEY, 10, int
    )


def _get_linode_cli_keys(
    keys_data: list,
    key_lifespan: str,
    key_rotation_period: str,
    current_timestamp: int,
) -> list:
    stale_threshold = current_timestamp - parse_time(key_lifespan)
    rotation_threshold = current_timestamp - parse_time(key_rotation_period)

    def extract_key_info(key: dict) -> Optional[dict]:
        match = re.match(r"^linode-cli-.+@.+-(\d{10,})$", key["label"])
        if not match:
            return None

        created_timestamp = int(match.group(1))
        is_stale = created_timestamp < stale_threshold
        needs_rotation = is_stale or created_timestamp <= rotation_threshold

        return {
            "id": key["id"],
            "label": key["label"],
            "access_key": key["access_key"],
            "created_timestamp": created_timestamp,
            "is_stale": is_stale,
            "needs_rotation": needs_rotation,
        }

    return sorted(
        [info for key in keys_data if (info := extract_key_info(key))],
        key=lambda k: k["created_timestamp"],
    )


def _rotate_current_key_if_needed(client: CLI, linode_cli_keys: list) -> None:
    current_access_key = client.config.plugin_get_value(ACCESS_KEY_KEY)

    key_to_rotate = next(
        (
            key_info
            for key_info in linode_cli_keys
            if key_info["access_key"] == current_access_key
            and key_info["needs_rotation"]
        ),
        None,
    )
    if key_to_rotate:
        _delete_key(client, key_to_rotate["id"], key_to_rotate["label"])
        linode_cli_keys.remove(key_to_rotate)
        client.config.plugin_remove_option(ACCESS_KEY_KEY)
        client.config.plugin_remove_option(SECRET_KEY_KEY)
        client.config.write_config()


def _delete_stale_keys(
    client: CLI, linode_cli_keys: list, batch_size: int
) -> None:
    stale_keys = [k for k in linode_cli_keys if k["is_stale"]]
    for key_info in stale_keys[:batch_size]:
        _delete_key(client, key_info["id"], key_info["label"])


def _delete_key(client: CLI, key_id: str, label: str) -> None:
    try:
        print(
            f"Deleting linode-cli Object Storage key: {label}", file=sys.stderr
        )
        status, _ = client.call_operation(
            "object-storage", "keys-delete", [str(key_id)]
        )
        if status != 200:
            print(
                f"Failed to delete key: {label}; status {status}",
                file=sys.stderr,
            )
    except Exception as e:
        print(
            f"Exception occurred while deleting key: {label}; {e}",
            file=sys.stderr,
        )
