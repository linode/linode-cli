from importlib import import_module
from os import listdir
from os.path import dirname

_available_files = listdir(dirname(__file__))
available = [f[:-3] for f in _available_files if f.endswith('.py') and f != '__init__.py']

def invoke(name, args, context):
    """
    Given the plugin name, executes a plugin
    """
    if name not in available:
        raise ValueError('No plugin named {}'.format(name))

    plugin = import_module('linodecli.plugins.'+name)
    plugin.call(args, context)
