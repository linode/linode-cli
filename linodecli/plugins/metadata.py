"""
This plugin allows users to access the metadata service while in a Linode.

Usage:

   linode-cli metadata [ENDPOINT]
"""

import argparse
import sys

from linode_metadata import MetadataClient
from linode_metadata.objects.error import ApiError
from linode_metadata.objects.instance import ResponseBase
from requests import ConnectTimeout
from rich import print as rprint
from rich.table import Table

PLUGIN_BASE = "linode-cli metadata"


def process_sub_columns(subcolumn: ResponseBase, table: Table, values_row):
    for key, value in vars(subcolumn).items():
        if isinstance(value, ResponseBase):
            process_sub_columns(value, table, values_row)
        else:
            table.add_column(key)
            values_row.append(str(value))


def print_single_row(data):
    attributes = vars(data)
    values_row = []

    table = Table()

    for key, value in attributes.items():
        if isinstance(value, ResponseBase):
            process_sub_columns(value, table, values_row)
        else:
            table.add_column(key)
            values_row.append(str(value))

    table.add_row(*values_row)
    rprint(table)

def print_ssh_keys(data):
    table = Table(show_lines=True)

    table.add_column("SSH Keys")
    for key in data.users.root:
        table.add_row(key)
    
    rprint(table)


def get_instance(client: MetadataClient):
    """
    Get information about your instance, including plan resources
    """
    data = client.get_instance()
    print_single_row(data)


def get_user_data(client: MetadataClient):
    """
    Get your user data
    """
    data = client.get_user_data()
    rprint(data)


def get_network(client: MetadataClient):
    """
    Get information about your instance’s IP addresses
    """
    data = client.get_network()
    print_single_row(data)


def get_ssh_keys(client: MetadataClient):
    """
    Get information about public SSH Keys configured on your instance
    """
    data = client.get_ssh_keys()
    print_ssh_keys(data)


COMMAND_MAP = {
    "instance": get_instance,
    "user-data": get_user_data,
    "network": get_network,
    "sshkeys": get_ssh_keys,
}


def print_help(parser: argparse.ArgumentParser):
    """
    Print out the help info to the standard output.
    """
    parser.print_help()

    # additional help
    print()
    print("Available endpoints: ")

    command_help_map = [
        [name, func.__doc__.strip()]
        for name, func in sorted(COMMAND_MAP.items())
    ]

    tab = Table(show_header=False)
    for row in command_help_map:
        tab.add_row(*row)
    rprint(tab)


def call(args, context):
    """
    The entrypoint for this plugin
    """

    parser = argparse.ArgumentParser(PLUGIN_BASE, add_help=False)

    parser.add_argument(
        "endpoint",
        metavar="ENDPOINT",
        nargs="?",
        type=str,
        help="The API endpoint to be called from the Metadata service.",
    )

    parsed, args = parser.parse_known_args(args)

    if not parsed.endpoint in COMMAND_MAP or len(args) != 0:
        print_help(parser)
        sys.exit(0)

    # make a client, but only if we weren't printing help and endpoint is valid
    if not "--help" in args:
        try:
            client = MetadataClient()
        except ConnectTimeout:
            print(
                "Can't access Metadata service. Please verify that you are inside a Linode."
            )
            sys.exit(0)
    else:
        print_help(parser)
        sys.exit(0)

    try:
        COMMAND_MAP[parsed.endpoint](client)
    except ApiError as e:
        sys.exit(f"Error: {e}")
