#!/usr/local/bin/python3
"""
Argument parser for the linode CLI
"""

import argparse
import os
import sys
from importlib.metadata import version
from sys import argv

from rich import print as rprint
from rich.table import Column, Table

from linodecli import plugins

from .arg_helpers import (
    bake_command,
    register_args,
    register_plugin,
    remove_plugin,
)
from .cli import CLI
from .completion import get_completions
from .configuration import ENV_TOKEN_NAME
from .help_pages import (
    HELP_TOPICS,
    print_help_action,
    print_help_commands,
    print_help_default,
    print_help_env_vars,
    print_help_plugins,
)
from .helpers import handle_url_overrides
from .output.output_handler import OutputMode
from .version import __version__

VERSION = __version__

BASE_URL = "https://api.linode.com/v4"

TEST_MODE = os.getenv("LINODE_CLI_TEST_MODE") == "1"

# if any of these arguments are given, we don't need to prompt for configuration
skip_config = (
    any(
        c in argv
        for c in ["--skip-config", "--help", "--version", "completion"]
    )
    or TEST_MODE
)

cli = CLI(VERSION, handle_url_overrides(BASE_URL), skip_config=skip_config)


def main():  # pylint: disable=too-many-branches,too-many-statements
    """
    Handle incoming command arguments
    """
    parser = argparse.ArgumentParser(
        "linode-cli",
        add_help=False,
        description="The Linode Command Line Interface.\n\nAliases: lin, linode",
    )
    parsed, args = register_args(parser).parse_known_args()

    cli.output_handler.configure(parsed, cli.suppress_warnings)

    if parsed.all_rows:
        cli.pagination = False

    cli.defaults = not parsed.no_defaults
    cli.retry_count = 0
    cli.no_retry = parsed.no_retry
    cli.suppress_warnings = parsed.suppress_warnings
    cli.page = parsed.page
    cli.page_size = parsed.page_size
    cli.debug_request = parsed.debug

    if parsed.as_user and not skip_config:
        cli.config.set_user(parsed.as_user)

    if parsed.version:
        if not parsed.command:
            # print version info and exit - but only if no command was given
            print(f"linode-cli {VERSION}")
            print(f"Built from spec version {cli.spec_version}")
            sys.exit(0)
        else:
            # something else might want to parse version
            # find where it was originally, as it was removed from args
            index = argv.index("--version") - 3  # executable command action
            args = args[:index] + ["--version"] + args[index:]

    # handle a bake - this is used to parse a spec and bake it as a pickle
    if parsed.command == "bake":
        if parsed.action is None:
            print("No spec provided, cannot bake")
            sys.exit(9)
        bake_command(cli, parsed.action)
        sys.exit(0)
    elif cli.ops is None:
        # if not spec was found and we weren't baking, we're doomed
        sys.exit(3)

    if parsed.command == "register-plugin":
        if parsed.action is None:
            print("register-plugin requires a module name!")
            sys.exit(9)
        msg, code = register_plugin(parsed.action, cli.config, cli.ops)
        print(msg)
        sys.exit(code)

    if parsed.command == "remove-plugin":
        if parsed.action is None:
            print("remove-plugin requires a plugin name to remove!")
            sys.exit(9)
        msg, code = remove_plugin(parsed.action, cli.config)
        print(msg)
        sys.exit(code)

    if parsed.command == "completion":
        print(get_completions(cli.ops, parsed.help, parsed.action))
        sys.exit(0)

    # handle a help for the CLI
    if parsed.command is None or (parsed.command is None and parsed.help):
        parser.print_help()
        print_help_default()
        sys.exit(0)

    if parsed.command == "env-vars":
        print_help_env_vars()
        sys.exit(0)

    if parsed.command == "commands":
        print_help_commands(cli.ops)
        sys.exit(0)

    if parsed.command == "plugins":
        print_help_plugins(cli.config)
        sys.exit(0)

    # configure
    if parsed.command == "configure":
        if parsed.help:
            print(
                "linode-cli configure\n\n"
                "Configured the Linode CLI.  This command can be used to change\n"
                "defaults selected for the current user, or to configure additional users."
            )
        else:
            cli.configure()
        sys.exit(0)

    # block of commands for user-focused operations
    if parsed.command == "set-user":
        if parsed.help or not parsed.action:
            print(
                "linode-cli set-user [USER]\n\n"
                "Sets the active user for the CLI out of users you have configured.\n"
                "To configure a new user, see `linode-cli configure`"
            )
        else:
            cli.config.set_default_user(parsed.action)
        sys.exit(0)

    if parsed.command == "show-users":
        if parsed.help:
            print(
                "linode-cli show-users\n\n"
                "Lists configured users.  Configured users can be set as the\n"
                "active user (used for all commands going forward) with the\n"
                "`set-user` command, or used for a single command with the\n"
                "`--as-user` flag.  New users can be added with `linode-cli configure`.\n"
                "The user that is currently active is indicated with a `*`"
            )
        else:
            cli.config.print_users()
        sys.exit(0)

    if parsed.command == "remove-user":
        if parsed.help or not parsed.action:
            print(
                "linode-cli remove-user [USER]\n\n"
                "Removes a user the CLI was configured with. This does not change\n"
                "your Linode account, only this CLI installation. Once removed,\n"
                "the user may not be set as active or used for commands unless\n"
                "configured again."
            )
        else:
            cli.config.remove_user(parsed.action)
        sys.exit(0)

    # check for plugin invocation
    if parsed.command not in cli.ops and parsed.command in plugins.available(
        cli.config
    ):
        context = plugins.PluginContext(cli.config.get_token(), cli)

        # reconstruct arguments to send to the plugin
        plugin_args = argv[1:]  # don't include the program name
        plugin_args.remove(parsed.command)  # don't include the plugin name
        plugins.invoke(parsed.command, plugin_args, context)
        sys.exit(0)

    # unknown commands
    if (
        parsed.command not in cli.ops
        and parsed.command not in plugins.available(cli.config)
        and parsed.command not in HELP_TOPICS
    ):
        print(f"Unrecognized command {parsed.command}")
        sys.exit(1)

    # handle a help for a command - either --help or no action triggers this
    if (
        parsed.command is not None
        and parsed.action is None
        and parsed.command in cli.ops
    ):
        print(f"linode-cli {parsed.command} [ACTION]")
        print()
        print("Available actions: ")

        content = [
            [", ".join([action, *op.action_aliases]), op.summary]
            for action, op in cli.ops[parsed.command].items()
        ]

        table = Table(
            Column(header="action", no_wrap=True),
            Column(header="summary", style="cyan"),
        )
        for row in content:
            table.add_row(*row)

        rprint(table)
        sys.exit(0)

    if parsed.command is not None and parsed.action is not None:
        if parsed.help:
            print_help_action(cli, parsed.command, parsed.action)
            sys.exit(0)
        cli.handle_command(parsed.command, parsed.action, args)
