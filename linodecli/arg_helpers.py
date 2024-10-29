#!/usr/local/bin/python3
"""
Argument parser for the linode CLI
"""
import sys
from importlib import import_module

from linodecli import plugins
from linodecli.helpers import (
    register_args_shared,
    register_debug_arg,
    register_pagination_args_shared,
)
from linodecli.output.helpers import register_output_args_shared


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

    register_output_args_shared(parser)
    register_pagination_args_shared(parser)
    register_args_shared(parser)
    register_debug_arg(parser)

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

    if plugin_name in plugins.AVAILABLE_LOCAL:
        msg = "Plugin name conflicts with internal CLI plugin - registration failed."
        return msg, 13

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
    if plugin_name in plugins.AVAILABLE_LOCAL:
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
