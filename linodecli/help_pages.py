"""
This module contains various helper functions related to outputting
help pages.
"""

import re
import textwrap
from collections import defaultdict
from typing import List, Optional

from rich import box
from rich import print as rprint
from rich.console import Console
from rich.padding import Padding
from rich.table import Table

from linodecli import plugins
from linodecli.baked import OpenAPIOperation
from linodecli.baked.request import OpenAPIRequestArg

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
}


# pylint: disable=too-many-locals
def print_help_default(ops, config):
    """
    Prints help output with options from the API spec
    """

    # Environment variables overrides
    print("\nEnvironment variables:")

    table = Table(show_header=True, header_style="", box=box.SQUARE)
    table.add_column("Name")
    table.add_column("Description")

    for k, v in HELP_ENV_VARS.items():
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
        "For comprehensive documentation, "
        "visit https://www.linode.com/docs/api/"
    )


def print_help_action(
    cli: "CLI", command: Optional[str], action: Optional[str]
):
    """
    Prints help relevant to the command and action
    """
    try:
        op = cli.find_operation(command, action)
    except ValueError:
        return

    console = Console(highlight=False)

    console.print(f"[bold]linode-cli {command} {action}[/]", end="")

    for param in op.params:
        pname = param.name.upper()
        console.print(f" [{pname}]", end="")

    console.print()
    console.print(f"[bold]{op.summary}[/]")

    if op.docs_url:
        console.print(
            f"[bold]API Documentation: [link={op.docs_url}]{op.docs_url}[/link][/]"
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

    if op.args:
        _help_action_print_body_args(console, op)


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
            console.print(f"  [bold magenta]--{attr.name}[/]")

        console.print(
            "\nAdditionally, you may order results using --order-by and --order."
        )


def _help_action_print_body_args(
    console: Console,
    op: OpenAPIOperation,
):
    """
    Pretty-prints all the body (POST/PUT) arguments for this operation.
    """
    console.print("[bold]Arguments:[/]")

    for group in _help_group_arguments(op.args):
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

            description = _markdown_links_to_rich(
                arg.description.replace("\n", " ").replace("\r", " ")
            )

            arg_str = (
                f"[bold magenta]--{arg.path}[/][bold]{prefix}[/]: {description}"
            )

            console.print(Padding.indent(arg_str.rstrip(), (arg.depth * 2) + 2))

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
                # Required arguments should come first in groups
                sorted(group, key=lambda v: not v.required),
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


def _markdown_links_to_rich(text):
    """
    Returns the given text with Markdown links converted to Rich-compatible links.
    """

    result = text

    # Find all Markdown links
    r = re.compile(r"\[(?P<text>.*?)]\((?P<link>.*?)\)")

    for match in r.finditer(text):
        url = match.group("link")

        # Expand the URL if necessary
        if url.startswith("/"):
            url = f"https://linode.com{url}"

        # Replace with more readable text
        result = result.replace(
            match.group(), f"{match.group('text')} ([link={url}]{url}[/link])"
        )

    return result
