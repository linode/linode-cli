"""
Initialize plugins for the CLI
"""
import sys
from importlib import import_module
from os import listdir
from os.path import dirname

_available_files = listdir(dirname(__file__))
available_local = [
    f[:-3] for f in _available_files if f.endswith(".py") and f != "__init__.py"
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

    def __init__(self, token, client):
        """
        Constructs a new PluginContext with the given information
        """
        self.token = token
        self.client = client
