Development
===========

The Linode CLI supports embedded plugins, features that are hard-coded (instead
of generated as the rest of the CLI is) but are accessible directly through the
CLI as other features are. All plugins are found in this directory.

Creating a Plugin
-----------------

To create a plugin, simply drop a new python file into this directory or write a
Python module that presents the interface described below. If the
plugin is a Python module, make sure the ``call`` method is in the ``__init__.py``
file in the root of the module.

Plugins in this directory are called "Internal Plugins," and must meet the
following conditions:

* Its name must be unique, both with the other plugins and with all commands
   offered through the generated CLI
* Its name must not contain special characters, and should be easily to enter
   on the command line
* It must contain a ``call(args, context)`` function for invocation
* It must support a ``--help`` command as all other CLI commands do.

Plugins that are installed separately and registered with the ``register-plugin``
command are called "Third Party Plugins," and must meet the following
conditions:

* Its name must be unique, both with the internal plugins and all CLI operations
* It must contain a ``call(args, context)`` function for invocation
* It must contain a ``PLUGIN_NAME`` constant whose value is a string that does not
   contain special characters, and should be easy to enter on the command line.
* It should support a `--help` command as all other CLI commands do.

The Plugin Interface
--------------------

All plugins are either an individual python file or a Python module
that reside in this directory or installed separately.  Plugins must have one function, ``call``, that
matches the following signature:

.. code-block:: python

    def call(args, context):
        """
        This is the function used to invoke the plugin.  It will receive the remainder
        of sys.argv after the plugin's name, and a context of user defaults and config
        settings.
        """

The PluginContext
^^^^^^^^^^^^^^^^^

The ``PluginContext`` class, passed as ``context`` to the ``call`` function, includes
all information the plugin is given during invocation.  This includes the following:

* ``token`` - The Personal Access Token registered with the CLI to make requests.
* ``client`` - The CLI Client object that can make authenticated requests on behalf
    of the acting user.  This is preferrable to using `requests` or another library
    directly (see below).

.. rubric:: CLI Client

The CLI Client provided as ``context.client`` can make authenticated API calls on
behalf of the user using the provided ``call_operation`` method.  This method is
invoked with a command and an action, and executes the given CLI command as if
it were entered into the command line, returning the resulting status code and
JSON data.

Configuration
-------------

Plugins can access the CLI's configuration through the CLI Client mentioned above.
Plugins are allowed to:

* Read values from the current user's config
* Read and write their own values to the current user's config

Any other operation is not supported and may break without notice.

Methods
^^^^^^^

The ``Configuration`` class provides the following methods for plugins to use:

**get_value(key)** Returns the value the current user has set for this key, or ``None``
if the key does not exist.  Currently supported keys are ``region``, ``type``, and ``image``.

**plugin_set_value(key, value)** Sets a value in the user's config for this plugin.
Plugins can safely set values for any key, and they are namespaced away from other
config keys.

**plugin_get_value(key)** Returns the value this plugin previously set for the given
key, or ``None`` if not set.  Plugins should assume they are not configured if they
receive ``None`` when getting a value with this method.

**write_config()** Writes config changes to disk.  This is required to save changes
after calling ``plugin_set_value`` above.

Sample Code
^^^^^^^^^^^

The following code manipulates and reads from the config in a plugin:

.. code-block:: python

    def call(args, context):
        # get a value from the user's config
        default_region = context.client.config.get_value('region')

        # check if we set a value previously
        our_value = context.client.config.plugin_get_value('configured')

        if our_value is None:
            # plugin not configured - do configuration here
            context.client.config.plugin_set_value('configured', 'yes')

            # save the config so changes take effect
            context.client.config.write_config()

        # normal plugin code

Development
-----------

To develop a plugin, simply create a python source file in this directory that
has a ``call`` function as described above.  To test, simply build the CLI as
normal (via ``make install``) or simply by running ``./setup.py install`` in the
root directory of the project (this installs the code without generating new
baked data, and will only work if you've installed the CLI via ``make install``
at least once, however it's a lot faster).

To develop a third party plugin, simply create and install your module and register
it to the CLI.  As long as the ``PLUGIN_NAME`` doesn't change, updated installations
should invoke the new code.

Examples
^^^^^^^^

This directory contains two example plugins, ``echo.py.example`` and
``regionstats.py.example``.  To run these, simply remove the ``.example`` at the end
of the file and build the CLI as described above.

`This directory <https://github.com/linode/linode-cli/tree/main/examples/third-party-plugin>`_
contains an example Third Party Plugin module.  This module is installable and
can be registered to the CLI.
