#!/usr/local/bin/python3
"""
Argument parser for the linode CLI
"""

import os
import sys
from importlib import import_module

import requests
import yaml
from rich import box
from rich import print as rprint
from rich.table import Table

from linodecli import plugins

from .completion import bake_completions
from .helpers import pagination_args_shared, register_args_shared


def register_args(parser):
    """
    Register static command arguments
    """
    parser.add_argument(
        "command",
        metavar="COMMAND",
        nargs="?",
        type=str,
        help="The command to invoke in the CLI.",
    )
    parser.add_argument(
        "action",
        metavar="ACTION",
        nargs="?",
        type=str,
        help="The action to perform in this command.",
    )
    parser.add_argument(
        "--help",
        action="store_true",
        help="Display information about a command, action, or the CLI overall.",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Display text output with a delimiter (defaults to tabs).",
    )
    parser.add_argument(
        "--delimiter",
        metavar="DELIMITER",
        type=str,
        help="The delimiter when displaying raw output.",
    )
    parser.add_argument(
        "--json", action="store_true", help="Display output as JSON."
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Display output in Markdown format.",
    )
    parser.add_argument(
        "--ascii-table",
        action="store_true",
        help="Display output in an ASCII table.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="If set, pretty-print JSON output.",
    )
    parser.add_argument(
        "--no-headers",
        action="store_true",
        help="If set, does not display headers in output.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Deprecated flag. An alias of '--all-columns', "
            "scheduled to be removed in a future version."
        ),
    )
    parser.add_argument(
        "--all-columns",
        action="store_true",
        help=(
            "If set, displays all possible columns instead of "
            "the default columns. This may not work well on some terminals."
        ),
    )
    parser.add_argument(
        "--format",
        metavar="FORMAT",
        type=str,
        help="The columns to display in output. Provide a comma-"
        "separated list of column names.",
    )
    parser.add_argument(
        "--no-defaults",
        action="store_true",
        help="Suppress default values for arguments.  Default values "
        "are configured on initial setup or with linode-cli configure",
    )
    parser.add_argument(
        "--no-truncation",
        action="store_true",
        default=False,
        help="Prevent the truncation of long values in command outputs.",
    )
    parser.add_argument(
        "--no-retry",
        action="store_true",
        help="Skip retrying on common errors like timeouts.",
    )
    parser.add_argument(
        "--single-table",
        action="store_true",
        help="Disable printing multiple tables for complex API responses.",
    )
    parser.add_argument(
        "--table",
        type=str,
        action="append",
        help="The specific table(s) to print in output of a command.",
    )
    parser.add_argument(
        "--column-width",
        type=int,
        default=None,
        help="Sets the maximum width of each column in outputted tables. "
        "By default, columns are dynamically sized to fit the terminal.",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Prints version information and exits.",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable verbose HTTP debug output."
    )

    pagination_args_shared(parser)
    register_args_shared(parser)

    return parser


# TODO: maybe move to plugins/__init__.py
def register_plugin(module, config, ops):
    """
    Handle registering a plugin
    Registering sets up the plugin for all CLI users
    """
    # attempt to import the module to prove it is installed and exists
    try:
        plugin = import_module(module)
    except ImportError:
        return f"Module {module} not installed", 10

    try:
        plugin_name = plugin.PLUGIN_NAME
    except AttributeError:
        msg = f"{module} is not a valid Linode CLI plugin - missing PLUGIN_NAME"
        return msg, 11

    try:
        call_func = plugin.call
        del call_func
    except AttributeError:
        msg = f"{module} is not a valid Linode CLI plugin - missing call"
        return msg, 11

    if plugin_name in ops:
        msg = "Plugin name conflicts with CLI operation - registration failed."
        return msg, 12

    if plugin_name in plugins.available_local:
        msg = "Plugin name conflicts with internal CLI plugin - registration failed."
        return msg, 13

    reregistering = False
    if plugin_name in plugins.available(config):
        print(f"WARNING: Plugin {plugin_name} is already registered.\n\n")
        answer = input(f"Allow re-registration of {plugin_name}? [y/N] ")
        if not answer or answer not in "yY":
            return "Registration aborted.", 0
        reregistering = True

    already_registered = []
    if config.config.has_option("DEFAULT", "registered-plugins"):
        already_registered = config.config.get(
            "DEFAULT", "registered-plugins"
        ).split(",")

    if reregistering:
        already_registered.remove(plugin_name)
        config.config.remove_option("DEFAULT", f"plugin-name-{plugin_name}")

    already_registered.append(plugin_name)
    config.config.set(
        "DEFAULT", "registered-plugins", ",".join(already_registered)
    )
    config.config.set("DEFAULT", f"plugin-name-{plugin_name}", module)
    config.write_config()

    msg = (
        "Plugin registered successfully!\n\n"
        "Invoke this plugin by running the following:\n\n"
        "  linode-cli {plugin_name}"
    )
    return msg, 0


# TODO: also maybe move to plugins
def remove_plugin(plugin_name, config):
    """
    Remove a plugin
    """
    if plugin_name in plugins.available_local:
        msg = f"{plugin_name} is bundled with the CLI and cannot be removed"
        return msg, 13

    if plugin_name not in plugins.available(config):
        msg = f"{plugin_name} is not a registered plugin"
        return msg, 14

    # do the removal
    current_plugins = config.config.get("DEFAULT", "registered-plugins").split(
        ","
    )
    current_plugins.remove(plugin_name)
    config.config.set(
        "DEFAULT", "registered-plugins", ",".join(current_plugins)
    )

    # if the config if malformed, don't blow up
    if config.config.has_option("DEFAULT", f"plugin-name-{plugin_name}"):
        config.config.remove_option("DEFAULT", f"plugin-name-{plugin_name}")

    config.write_config()
    return f"Plugin {plugin_name} removed", 0


# pylint: disable=too-many-locals
def help_with_ops(ops, config):
    """
    Prints help output with options from the API spec
    """

    # Environment variables overrides
    print("\nEnvironment variables:")
    env_variables = {
        "LINODE_CLI_TOKEN": "A Linode Personal Access Token for the CLI to make requests with. "
        "If specified, the configuration step will be skipped.",
        "LINODE_CLI_CA": "The path to a custom Certificate Authority file to verify "
        "API requests against.",
        "LINODE_CLI_API_HOST": "Overrides the target host for API requests. "
        "(e.g. 'api.linode.com')",
        "LINODE_CLI_API_VERSION": "Overrides the target Linode API version for API requests. "
        "(e.g. 'v4beta')",
        "LINODE_CLI_API_SCHEME": "Overrides the target scheme used for API requests. "
        "(e.g. 'https')",
    }

    table = Table(show_header=True, header_style="", box=box.SQUARE)
    table.add_column("Name")
    table.add_column("Description")

    for k, v in env_variables.items():
        table.add_row(k, v)

    rprint(table)

    # commands to manage CLI users (don't call out to API)
    print("\nCLI user management commands:")
    um_commands = [["configure", "set-user", "show-users"], ["remove-user"]]
    table = Table(show_header=False)
    for cmd in um_commands:
        table.add_row(*cmd)
    rprint(table)

    # commands to manage plugins (don't call out to API)
    print("\nCLI Plugin management commands:")
    pm_commands = [["register-plugin", "remove-plugin"]]
    table = Table(show_header=False)
    for cmd in pm_commands:
        table.add_row(*cmd)
    rprint(table)

    # other CLI commands
    print("\nOther CLI commands:")
    other_commands = [["completion"]]
    table = Table(show_header=False)
    for cmd in other_commands:
        table.add_row(*cmd)
    rprint(table)

    # commands generated from the spec (call the API directly)
    print("\nAvailable commands:")

    content = list(sorted(ops.keys()))
    proc = []
    for i in range(0, len(content), 3):
        proc.append(content[i : i + 3])
    if content[i + 3 :]:
        proc.append(content[i + 3 :])

    table = Table(show_header=False)
    for cmd in proc:
        table.add_row(*cmd)
    rprint(table)

    # plugins registered to the CLI (do arbitrary things)
    if plugins.available(config):
        # only show this if there are any available plugins
        print("Available plugins:")

        plugin_content = list(plugins.available(config))
        plugin_proc = []

        for i in range(0, len(plugin_content), 3):
            plugin_proc.append(plugin_content[i : i + 3])
        if plugin_content[i + 3 :]:
            plugin_proc.append(plugin_content[i + 3 :])

        plugin_table = Table(show_header=False)
        for plugin in plugin_proc:
            plugin_table.add_row(*plugin)
        rprint(plugin_table)

    print("\nTo reconfigure, call `linode-cli configure`")
    print(
        "For comprehensive documentation,"
        "visit https://www.linode.com/docs/api/"
    )


def action_help(cli, command, action):
    """
    Prints help relevant to the command and action
    """
    try:
        op = cli.find_operation(command, action)
    except ValueError:
        return
    print(f"linode-cli {command} {action}", end="")
    for param in op.params:
        pname = param.name.upper()
        print(f" [{pname}]", end="")
    print()
    print(op.summary)
    if op.docs_url:
        print(f"API Documentation: {op.docs_url}")
    print()
    if op.method == "get" and op.action == "list":
        filterable_attrs = [
            attr for attr in op.response_model.attrs if attr.filterable
        ]

        if filterable_attrs:
            print("You may filter results with:")
            for attr in filterable_attrs:
                print(f"  --{attr.name}")
            print(
                "Additionally, you may order results using --order-by and --order."
            )
        return
    if op.args:
        print("Arguments:")
        for arg in sorted(op.args, key=lambda s: not s.required):
            if arg.read_only:
                continue
            is_required = (
                "(required) "
                if op.method in {"post", "put"} and arg.required
                else ""
            )
            nullable_fmt = " (nullable)" if arg.nullable else ""
            print(
                f"  --{arg.path}: {is_required}{arg.description}{nullable_fmt}"
            )


def bake_command(cli, spec_loc):
    """
    Handle a bake command from args
    """
    try:
        if os.path.exists(os.path.expanduser(spec_loc)):
            with open(os.path.expanduser(spec_loc), encoding="utf-8") as f:
                spec = yaml.safe_load(f.read())
        else:  # try to GET it
            resp = requests.get(spec_loc, timeout=120)
            if resp.status_code == 200:
                spec = yaml.safe_load(resp.content)
            else:
                raise RuntimeError(f"Request failed to {spec_loc}")
    except Exception as e:
        print(f"Could not load spec: {e}")
        sys.exit(2)

    cli.bake(spec)
    bake_completions(cli.ops)
