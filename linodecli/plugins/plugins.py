"""
Initialize plugins for the CLI
"""

import sys
from argparse import ArgumentParser
from importlib import import_module
from pathlib import Path
from typing import List

from linodecli.cli import CLI
from linodecli.configuration import CLIConfig
from linodecli.exit_codes import ExitCodes
from linodecli.helpers import register_args_shared

THIS_FILE = Path(__file__)

# Contains a list of files/directories to ignore
# when searching for plugins.
RESERVED_FILES = {THIS_FILE, THIS_FILE.parent / "__init__.py"}


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


def is_single_file_plugin(f: Path) -> bool:
    """
    Determine if the file is a single-file plugin.

    :param f: The path of the file to identify.
    :type f: Path

    :returns: Whether the given file is a single-file plugin.
    :rtype: bool
    """
    return f.suffix == ".py"


def is_module_plugin(f: Path) -> bool:
    """
    Determine if the file is a module (directory) based plugin.

    :param f: The path of the file to identify.
    :type f: Path

    :returns: Whether the given file is a module plugin.
    :rtype: bool
    """
    return f.is_dir() and f.name[:1] != "_"


def is_plugin(f: Path) -> bool:
    """
    Determine if the file is a linode-cli plugin.

    :param f: The path of the file to validate against.
    :type f: Path

    :returns: Whether the given file is a plugin.
    :rtype: bool
    """
    if f in RESERVED_FILES:
        return False

    return is_module_plugin(f) or is_single_file_plugin(f)


AVAILABLE_LOCAL = [
    f.stem for f in Path.iterdir(THIS_FILE.parent) if is_plugin(f)
]


def available(config: CLIConfig) -> List[str]:
    """
    Returns a list of plugins that are available.

    :param config: The Linode CLI config to reference.
    :type config: CLIConfig

    :returns: A list of all available plugins.
    :rtype: List[str]
    """

    additional = []

    if config.config.has_option("DEFAULT", "registered-plugins"):
        registered_plugins = config.config.get("DEFAULT", "registered-plugins")

        additional = registered_plugins.split(",")

    return AVAILABLE_LOCAL + additional


def invoke(name: str, args: List[str], context: PluginContext):
    """
    Invokes a plugin based on the given name, arguments, and plugin context.

    :param name: The name of the plugin to invoke.
    :type name: str
    :param args: A list of arguments passed into the plugin CLI.
    :type args: List[str]
    :param context: The PluginContext containing data about the CLI, configuration, etc.
    :type context: PluginContext
    @param args: A list of string arguments passed to the plugin.
    """
    # setup config to know what plugin is running
    context.client.config.running_plugin = name

    if name in AVAILABLE_LOCAL:
        # If this is a local plugin, import it with the adjusted module prefix
        plugin = import_module("linodecli.plugins." + name)
    elif name in available(context.client.config):
        # If this is a third-party plugin, retrieve its module name from the config
        try:
            plugin_module_name = context.client.config.config.get(
                "DEFAULT", f"plugin-name-{name}"
            )
        except KeyError:
            print(
                f"Plugin {name} is misconfigured - please re-register it",
                file=sys.stderr,
            )
            sys.exit(ExitCodes.REQUEST_FAILED)

        try:
            plugin = import_module(plugin_module_name)
        except ImportError:
            print(
                f"Expected module '{plugin_module_name}' not found.  "
                "Either {name} is misconfigured, or the backing module was uninstalled.",
                file=sys.stderr,
            )
            sys.exit(ExitCodes.REQUEST_FAILED)
    else:
        raise ValueError("No plugin named {name}")

    plugin.call(args, context)


def inherit_plugin_args(parser: ArgumentParser) -> ArgumentParser:
    """
    This function allows plugin-defined ArgumentParsers to inherit
    certain CLI configuration arguments (`--as-user`, etc.).

    These arguments will be automatically applied to the CLI instance
    provided in the PluginContext object.

    :param parser: The argument parser to be supplied shared arguments.
    :type parser: ArgumentParser

    :returns: The updated argument parser.
    :rtype: ArgumentParser
    """

    return register_args_shared(parser)
