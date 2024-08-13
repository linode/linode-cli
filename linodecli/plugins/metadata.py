"""
This plugin allows users to access the metadata service while in a Linode.

Usage:

   linode-cli metadata [ENDPOINT]
"""

import sys
from argparse import ArgumentParser

from linode_metadata import MetadataClient
from linode_metadata.objects.error import ApiError
from linode_metadata.objects.instance import ResponseBase
from requests import ConnectTimeout
from rich import print as rprint
from rich.table import Table

from linodecli.exit_codes import ExitCodes
from linodecli.helpers import register_debug_arg

PLUGIN_BASE = "linode-cli metadata"


def process_sub_columns(subcolumn: ResponseBase, table: Table, values_row):
    """
    Helper method to process embedded ResponseBase objects
    """
    for key, value in vars(subcolumn).items():
        if isinstance(value, ResponseBase):
            process_sub_columns(value, table, values_row)
        else:
            table.add_column(key)
            values_row.append(str(value))


def print_instance_table(data):
    """
    Prints the table that contains information about the current instance
    """
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


def print_ssh_keys_table(data):
    """
    Prints the table that contains information about the SSH keys for the current instance
    """
    table = Table(show_lines=True)

    table.add_column("user")
    table.add_column("ssh key")

    for name, keys in data.users.items():
        # Keys will be None if no keys are configured for the user
        if keys is None:
            continue

        for key in keys:
            table.add_row(name, key)

    rprint(table)


def print_networking_tables(data):
    """
    Prints the table that contains information about the network of the current instance
    """
    interfaces = Table(title="Interfaces", show_lines=True)

    interfaces.add_column("label")
    interfaces.add_column("purpose")
    interfaces.add_column("ipam addresses")

    for interface in data.interfaces:
        attributes = vars(interface)
        interface_row = []
        for _, value in attributes.items():
            interface_row.append(str(value))
        interfaces.add_row(*interface_row)

    ipv4 = Table(title="IPv4")
    ipv4.add_column("ip address")
    ipv4.add_column("type")
    attributes = vars(data.ipv4)
    for key, value in attributes.items():
        for address in value:
            ipv4.add_row(*[address, key])

    ipv6 = Table(title="IPv6")
    ipv6_data = data.ipv6
    ipv6.add_column("slaac")
    ipv6.add_column("link local")
    ipv6.add_column("ranges")
    ipv6.add_column("shared ranges")
    ipv6.add_row(
        *[
            ipv6_data.slaac,
            ipv6_data.link_local,
            str(ipv6_data.ranges),
            str(ipv6_data.shared_ranges),
        ]
    )

    rprint(interfaces)
    rprint(ipv4)
    rprint(ipv6)


def get_instance(client: MetadataClient):
    """
    Get information about your instance, including plan resources
    """
    data = client.get_instance()
    print_instance_table(data)


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
    print_networking_tables(data)


def get_ssh_keys(client: MetadataClient):
    """
    Get information about public SSH Keys configured on your instance
    """
    data = client.get_ssh_keys()
    print_ssh_keys_table(data)


COMMAND_MAP = {
    "instance": get_instance,
    "user-data": get_user_data,
    "networking": get_network,
    "sshkeys": get_ssh_keys,
}


def print_help(parser: ArgumentParser):
    """
    Print out the help info to the standard output
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


def get_metadata_parser():
    """
    Builds argparser for Metadata plug-in
    """
    parser = ArgumentParser(PLUGIN_BASE, add_help=False)

    register_debug_arg(parser)

    parser.add_argument(
        "endpoint",
        metavar="ENDPOINT",
        nargs="?",
        type=str,
        help="The API endpoint to be called from the Metadata service.",
    )

    return parser


def call(args, context):
    """
    The entrypoint for this plugin
    """

    parser = get_metadata_parser()
    parsed, args = parser.parse_known_args(args)

    if not parsed.endpoint in COMMAND_MAP or len(args) != 0:
        print_help(parser)
        sys.exit(ExitCodes.SUCCESS)

    # make a client, but only if we weren't printing help and endpoint is valid
    if "--help" not in args:
        try:
            client = MetadataClient(
                user_agent=context.client.user_agent, debug=parsed.debug
            )
        except ConnectTimeout as exc:
            raise ConnectionError(
                "Can't access Metadata service. Please verify that you are inside a Linode."
            ) from exc
    else:
        print_help(parser)
        sys.exit(ExitCodes.SUCCESS)

    try:
        COMMAND_MAP[parsed.endpoint](client)
    except ApiError:
        sys.exit(ExitCodes.REQUEST_FAILED)
