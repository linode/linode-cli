#!/usr/local/bin/python3
"""
Argument parser for the linode CLI.
This module defines argument parsing, plugin registration, and plugin removal
functionalities for the Linode CLI.
"""
import sys
from argparse import ArgumentParser
from configparser import ConfigParser
from importlib import import_module
from typing import Dict, Tuple

from linodecli import plugins
from linodecli.helpers import (
    register_args_shared,
    register_debug_arg,
    register_pagination_args_shared,
)
from linodecli.output.helpers import register_output_args_shared


def register_args(parser: ArgumentParser) -> ArgumentParser:
    """
    Register static command arguments for the Linode CLI.

    :param parser: Argument parser object to which arguments will be added.

    :return: The updated ArgumentParser instance.
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
        "--no-defaults",
        action="store_true",
        help="Suppress default values for arguments.  Default values "
        "are configured on initial setup or with linode-cli configure",
    )

    parser.add_argument(
        "--no-retry",
        action="store_true",
        help="Skip retrying on common errors like timeouts.",
    )

    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Prints version information and exits.",
    )

    parser.add_argument(
        "--alias-command",
        nargs="?",
        type=str,
        help="The command to set or remove an alias for.",
    )

    parser.add_argument(
        "--alias",
        nargs="?",
        type=str,
        help="The alias to set or remove.",
    )

    # Register shared argument groups
    register_output_args_shared(parser)
    register_pagination_args_shared(parser)
    register_args_shared(parser)
    register_debug_arg(parser)

    return parser


# TODO: maybe move to plugins/__init__.py
def register_plugin(
    module: str, config: ConfigParser, ops: Dict[str, str]
) -> Tuple[str, int]:
    """
    Handle registering a plugin for the Linode CLI.

    :param module: The name of the module to be registered as a plugin.
    :param config: Configuration parser object.
    :param ops: Dictionary of existing CLI operations.

    :return: A tuple containing a message and an exit code.
    """

    # Attempt to import the module to prove it is installed and exists
    try:
        plugin = import_module(module)
    except ImportError:
        return f"Module {module} not installed", 10

    # Ensure the module defines a PLUGIN_NAME attribute
    try:
        plugin_name = plugin.PLUGIN_NAME
    except AttributeError:
        msg = f"{module} is not a valid Linode CLI plugin - missing PLUGIN_NAME"
        return msg, 11

    # Ensure the module has a 'call' function, which is required for execution
    try:
        call_func = plugin.call
        del call_func  # Just checking if it exists, so we can discard it
    except AttributeError:
        msg = f"{module} is not a valid Linode CLI plugin - missing call"
        return msg, 11

    # Check if the plugin name conflicts with existing CLI operations
    if plugin_name in ops:
        msg = "Plugin name conflicts with CLI operation - registration failed."
        return msg, 12

    # Check if the plugin name conflicts with an internal CLI plugin
    if plugin_name in plugins.AVAILABLE_LOCAL:
        msg = "Plugin name conflicts with internal CLI plugin - registration failed."
        return msg, 13

    # Check if the plugin is already registered and ask for re-registration if needed
    reregistering = False
    if plugin_name in plugins.available(config):
        print(
            f"WARNING: Plugin {plugin_name} is already registered.\n\n",
            file=sys.stderr,
        )
        answer = input(f"Allow re-registration of {plugin_name}? [y/N] ")
        if not answer or answer not in "yY":
            return "Registration aborted.", 0
        reregistering = True

    # Retrieve the list of already registered plugins from the config
    already_registered = []
    if config.config.has_option("DEFAULT", "registered-plugins"):
        already_registered = config.config.get(
            "DEFAULT", "registered-plugins"
        ).split(",")

    # If re-registering, remove the existing entry before adding it again
    if reregistering:
        already_registered.remove(plugin_name)
        config.config.remove_option("DEFAULT", f"plugin-name-{plugin_name}")

    # Add the new plugin to the registered list
    already_registered.append(plugin_name)
    config.config.set(
        "DEFAULT", "registered-plugins", ",".join(already_registered)
    )

    # Store the module name associated with this plugin in the config
    # and save the updated config to persist changes
    config.config.set("DEFAULT", f"plugin-name-{plugin_name}", module)
    config.write_config()

    msg = (
        "Plugin registered successfully!\n\n"
        "Invoke this plugin by running the following:\n\n"
        "  linode-cli {plugin_name}"
    )
    return msg, 0


# TODO: also maybe move to plugins
def remove_plugin(plugin_name: str, config: ConfigParser) -> Tuple[str, int]:
    """
    Remove a registered plugin from the Linode CLI.

    :param plugin_name: The name of the plugin to remove.
    :param config: Configuration parser object that manages CLI settings.

    :return: A tuple containing a message and an exit code.
    """

    # Check if the plugin is a built-in CLI plugin that cannot be removed
    if plugin_name in plugins.AVAILABLE_LOCAL:
        msg = f"{plugin_name} is bundled with the CLI and cannot be removed"
        return msg, 13

    # Check if the plugin is actually registered before attempting removal
    if plugin_name not in plugins.available(config):
        msg = f"{plugin_name} is not a registered plugin"
        return msg, 14

    # Do the removal
    current_plugins = config.config.get("DEFAULT", "registered-plugins").split(
        ","
    )
    current_plugins.remove(plugin_name)
    config.config.set(
        "DEFAULT", "registered-plugins", ",".join(current_plugins)
    )

    # If the config is malformed, don't blow up
    if config.config.has_option("DEFAULT", f"plugin-name-{plugin_name}"):
        config.config.remove_option("DEFAULT", f"plugin-name-{plugin_name}")

    config.write_config()
    return f"Plugin {plugin_name} removed", 0
