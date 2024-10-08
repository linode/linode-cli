.. _general_plugins:

Plugins
=======

The Linode CLI allows its features to be expanded with plugins.  Some official
plugins come bundled with the CLI and are documented above.  Additionally, anyone
can write and distribute plugins for the CLI - these are called Third Party Plugins.

To register a Third Party Plugin, use the following command::

    linode-cli register-plugin PLUGIN_MODULE_NAME

Plugins should give the exact command required to register them.

Once registered, the command to invoke the Third Party Plugin will be printed, and
it will appear in the plugin list when invoking ``linode-cli --help``.

To remove a previously registered plugin, use the following command::

    linode-cli remove-plugin PLUGIN_NAME

This command accepts the name used to invoke the plugin in the CLI as it appears
in ``linode-cli --help``, which may not be the same as the module name used to
register it.

Developing Plugins
------------------

For information on how To write your own Third Party Plugin, see the
:ref:`Plugins documentation <plugins>`.
