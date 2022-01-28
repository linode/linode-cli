"""
This file is an example third-party plugin.  See `the plugin docs`_ for more
information.

.. _the plugin docs: https://github.com/linode/linode-cli/blob/master/linodecli/plugins/README.md
"""

#: This is the name the plugin will be invoked with once it's registered.  Note
#: that this name is different than the module name, which is what's used to
#: register it.  This is required for all third party plugins.
PLUGIN_NAME = "example-plugin"


def call(args, context):
    """
    This is the entrypoint for the plugin when invoked through the CLI.  See the
    docs linked above for more information.
    """
    print("Hello world!")
