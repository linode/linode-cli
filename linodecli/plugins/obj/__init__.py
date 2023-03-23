# pylint: disable=too-many-lines
"""
CLI Plugin for handling OBJ
"""
import sys
from argparse import ArgumentParser
from contextlib import suppress
from math import ceil
from typing import List

from terminaltables import SingleTable

from linodecli.cli import CLI
from linodecli.configuration import _do_get_request
from linodecli.configuration.helpers import _default_thing_input
from linodecli.helpers import expand_globs
from linodecli.plugins import PluginContext, inherit_plugin_args
from linodecli.plugins.obj.acl import set_acl
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
    _configure_plugin,
    _convert_datetime,
    _denominate,
    _get_s3_creds,
    _pad_to,
    _progress,
    get_credentials,
    regenerate_s3_credentials,
    restricted_int_arg_type,
)
from linodecli.plugins.obj.list import list_all_objects, list_objects_or_buckets
from linodecli.plugins.obj.objects import (
    delete_object,
    get_object,
    upload_object,
)
from linodecli.plugins.obj.url import generate_url
from linodecli.plugins.obj.usage import show_usage
from linodecli.plugins.obj.website import (
    disable_static_site,
    enable_static_site,
    static_site_info,
)

try:
    import boto3
    from botocore.exceptions import ClientError

    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


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
    client.cluster = cluster
    return client
