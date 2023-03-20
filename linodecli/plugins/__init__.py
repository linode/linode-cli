"""
Initialize plugins for the CLI
"""
import sys
from argparse import ArgumentParser
from importlib import import_module
from os import listdir
from os.path import dirname
from pathlib import Path

from linodecli.cli import CLI
from linodecli.helpers import register_args_shared

this_file = Path(__file__)
reserved_files = {this_file}


def is_single_file_plugin(f: Path):
    """
    Determine if the file is a single-file plugin.
    """
    return f.suffix == ".py"


def is_module_plugin(f: Path):
    """
    Determine if the file is a module (directory) based plugin.
    """
    return f.is_dir() and f.name[:1] != "_"


def is_plugin(f: Path):
    """
    Determine if the file is a linode-cli plugin.
    """
    if f in reserved_files:
        return False
    return is_module_plugin(f) or is_single_file_plugin(f)


available_local = [
    f.stem for f in Path.iterdir(this_file.parent) if is_plugin(f)
]


def available(config):
    """
    Returns a list of plugins that are available
    """
    additional = []
    if config.config.has_option("DEFAULT", "registered-plugins"):
        registered_plugins = config.config.get("DEFAULT", "registered-plugins")

        additional = registered_plugins.split(",")

    return available_local + additional


def invoke(name, args, context):
    """
    Given the plugin name, executes a plugin
    """
    # setup config to know what plugin is running
    context.client.config.running_plugin = name

    if name in available_local:
        plugin = import_module("linodecli.plugins." + name)
        plugin.call(args, context)
    elif name in available(context.client.config):
        # this is a third-party plugin
        try:
            plugin_module_name = context.client.config.config.get(
                "DEFAULT", f"plugin-name-{name}"
            )
        except KeyError:
            print(f"Plugin {name} is misconfigured - please re-register it")
            sys.exit(9)
        try:
            plugin = import_module(plugin_module_name)
        except ImportError:
            print(
                f"Expected module '{plugin_module_name}' not found.  "
                "Either {name} is misconfigured, or the backing module was uninstalled."
            )
            sys.exit(10)
        plugin.call(args, context)
    else:
        raise ValueError("No plugin named {name}")


class PluginContext:  # pylint: disable=too-few-public-methods
    """
    This class contains all context information provided to plugins when invoked.
    This includes access to the underlying CLI object to access the user's account,
    and the CLI access token the user has provided.
    """

    def __init__(self, token: str, client: CLI):
        """
        Constructs a new PluginContext with the given information
        """
        self.token = token
        self.client = client


def inherit_plugin_args(parser: ArgumentParser):
    """
    This function allows plugin-defined ArgumentParsers to inherit
    certain CLI configuration arguments (`--as-user`, etc.).

    These arguments will be automatically applied to the CLI instance
    provided in the PluginContext object.
    """

    return register_args_shared(parser)
