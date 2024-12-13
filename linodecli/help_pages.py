"""
This module contains various helper functions related to outputting
help pages.
"""

import sys
import textwrap
from collections import defaultdict
from typing import Dict, List, Optional

from rich import box
from rich import print as rprint
from rich.console import Console
from rich.padding import Padding
from rich.table import Column, Table
from rich.text import Text

from linodecli.baked import OpenAPIOperation
from linodecli.baked.request import OpenAPIRequestArg
from linodecli.exit_codes import ExitCodes
from linodecli.plugins import plugins

HELP_ENV_VARS = {
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
    "LINODE_CLI_CONFIG": "Overrides the default configuration file path. "
    "(e.g '~/.linode/my-cli-config')",
}

HELP_TOPICS = {
    "env-vars": "Environment variables that can be used",
    "commands": "Learn about all available commands with linode-cli",
    "plugins": " Learn about all available plugins registered to linode-cli",
}


def print_help_env_vars():
    """
    Print Environment variables overrides. Usage:

        linode-cli env-vars
    """
    rprint("\n[bold cyan]Environment variables:")

    table = Table(show_header=True, header_style="bold", box=box.SQUARE)
    table.add_column("Name")
    table.add_column("Description")

    for k, v in HELP_ENV_VARS.items():
        table.add_row(k, v)

    rprint(table)


def print_help_commands(ops):
    """
    Prints available commands. Usage:

        linode-cli commands
    """
    # commands to manage CLI users (don't call out to API)
    rprint("\n[bold cyan]CLI user management commands:")
    um_commands = [["configure", "set-user", "show-users"], ["remove-user"]]
    table = Table(show_header=False)
    for cmd in um_commands:
        table.add_row(*cmd)
    rprint(table)

    # commands to manage plugins (don't call out to API)
    rprint("\n[bold cyan]CLI Plugin management commands:")
    pm_commands = [["register-plugin", "remove-plugin"]]
    table = Table(show_header=False)
    for cmd in pm_commands:
        table.add_row(*cmd)
    rprint(table)

    # other CLI commands
    rprint("\n[bold cyan]Other CLI commands:")
    other_commands = [["completion"]]
    table = Table(show_header=False)
    for cmd in other_commands:
        table.add_row(*cmd)
    rprint(table)

    # commands generated from the spec (call the API directly)
    rprint("\n[bold cyan]Available commands:")

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


def print_help_plugins(config):
    """
    Print available plugins registered to the CLI (do arbitrary things). Usage:

        linode-cli plugins
    """
    if plugins.available(config):
        # only show this if there are any available plugins
        rprint("\n[bold cyan]Available plugins:")

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


def print_help_default():
    """
    Prints help output with options from the API spec
    """
    rprint("\n[bold cyan]Help Topics")
    for k, v in HELP_TOPICS.items():
        print("  " + k + ": " + v)
    rprint("\n[bold]To reconfigure[/], call `linode-cli configure`")
    print(
        "For comprehensive documentation, "
        "visit https://www.linode.com/docs/api/"
    )


def print_help_command_actions(
    ops: Dict[str, Dict[str, OpenAPIOperation]],
    command: Optional[str],
    file=sys.stdout,
):
    """
    Prints the help page for a single command, including all actions
    under the given command.

    :param ops: A dictionary mapping CLI commands -> actions -> operations.
    :param command: The command to print the help page for.
    """

    print(f"linode-cli {command} [ACTION]\n\nAvailable actions: ", file=file)

    content = [
        [", ".join([action, *op.action_aliases]), op.summary]
        for action, op in sorted(ops[command].items(), key=lambda v: v[0])
    ]

    table = Table(
        Column(header="action", no_wrap=True),
        Column(header="summary", style="cyan"),
    )
    for row in content:
        table.add_row(*row)

    rprint(table, file=file)


def print_help_action(
    cli: "CLI", command: Optional[str], action: Optional[str]
):
    """
    Prints help relevant to the command and action
    """
    try:
        op = cli.find_operation(command, action)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(ExitCodes.UNRECOGNIZED_ACTION)

    console = Console(highlight=False)

    console.print(f"[bold]linode-cli {command} {action}[/]", end="")

    for param in op.params:
        pname = param.name.upper()
        console.print(f" [{pname}]", end="")

    console.print()
    console.print(f"[cyan]{op.summary}[/]")

    if op.docs_url:
        console.print(
            f"[bold]API Documentation[/]: [link={op.docs_url}]{op.docs_url}[/link]"
        )

    if len(op.samples) > 0:
        console.print()
        console.print(
            f"[bold]Example Usage{'s' if len(op.samples) > 1 else ''}: [/]"
        )

        console.print(
            *[
                # Indent all samples for readability; strip and trailing newlines
                textwrap.indent(v.get("source").rstrip(), "  ")
                for v in op.samples
            ],
            sep="\n\n",
            highlight=True,
        )

    console.print()

    if op.method == "get" and op.response_model.is_paginated:
        _help_action_print_filter_args(console, op)
        return

    if len(op.arg_routes) > 0:
        # This operation uses oneOf so we need to render routes
        # instead of the operation-level argument list.
        for title, option in op.arg_routes.items():
            _help_action_print_body_args(console, op, option, title=title)
    elif op.args:
        _help_action_print_body_args(console, op, op.args)


def _help_action_print_filter_args(console: Console, op: OpenAPIOperation):
    """
    Pretty-prints all the filter (GET) arguments for this operation.
    """

    filterable_attrs = [
        attr for attr in op.response_model.attrs if attr.filterable
    ]

    if filterable_attrs:
        console.print("[bold]You may filter results with:[/]")
        for attr in filterable_attrs:
            console.print(f"  [bold green]--{attr.name}[/]")

        console.print(
            "\nAdditionally, you may order results using --order-by and --order."
        )


def _help_action_print_body_args(
    console: Console,
    op: OpenAPIOperation,
    args: List[OpenAPIRequestArg],
    title: Optional[str] = None,
):
    """
    Pretty-prints all the body (POST/PUT) arguments for this operation.
    """
    console.print(f"[bold]Arguments{f' ({title})' if title else ''}:[/]")

    for group in _help_group_arguments(args):
        for arg in group:
            metadata = []

            if op.method in {"post", "put"} and arg.required:
                metadata.append("required")

            if arg.format == "json":
                metadata.append("JSON")

            if arg.nullable:
                metadata.append("nullable")

            if arg.is_parent:
                metadata.append("conflicts with children")

            prefix = f" ({', '.join(metadata)})" if len(metadata) > 0 else ""

            arg_text = Text.from_markup(
                f"[bold green]--{arg.path}[/][bold]{prefix}:[/] {arg.description_rich}"
            )

            console.print(
                Padding.indent(arg_text, (arg.depth * 2) + 2),
            )

        console.print()


def _help_group_arguments(
    args: List[OpenAPIRequestArg],
) -> List[List[OpenAPIRequestArg]]:
    """
    Returns help page groupings for a list of POST/PUT arguments.
    """
    args_sorted = sorted(args, key=lambda a: a.path)

    groups_tmp = defaultdict(list)

    # Initial grouping by root parent
    for arg in args_sorted:
        if arg.read_only:
            continue

        groups_tmp[arg.path.split(".", 1)[0]].append(arg)

    group_required = []
    groups = []
    ungrouped = []

    for group in groups_tmp.values():
        # If the group has more than one element,
        # leave it as is in the result
        if len(group) > 1:
            groups.append(
                # Args should be ordered by least depth -> required -> path
                sorted(group, key=lambda v: (v.depth, not v.required, v.path)),
            )
            continue

        target_arg = group[0]

        # If the group's argument is required,
        # add it to the required group
        if target_arg.required:
            group_required.append(target_arg)
            continue

        # Add ungrouped arguments (single value groups) to the
        # "ungrouped" group.
        ungrouped.append(target_arg)

    result = []

    if len(group_required) > 0:
        result.append(group_required)

    if len(ungrouped) > 0:
        result.append(ungrouped)

    result += groups

    return result
