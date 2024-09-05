.. _general_configuration:

Configuration
=============

The first time the CLI runs, it will prompt you to configure it.  The CLI defaults
to using web-based configuration, which is fast and convenient for users who
have access to a browser.

To manually configure the CLI or reconfigure it if your token expires, you can
run the ``configure`` command::

    linode-cli configure

If you prefer to provide a token directly through the terminal, possibly because
you don't have access to a browser where you're configuring the CLI, pass the
``--token`` flag to the configure command as shown::

    linode-cli configure --token

When configuring multiple users using web-based configuration, you may need to
log out of cloud.linode.com before configuring a second user.

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

If you prefer, you may store your token in an environment variable named
``LINODE_CLI_TOKEN`` instead of using the configuration file.  Doing so allows you
to bypass the initial configuration, and subsequent calls to ``linode-cli configure``
will allow you to set defaults without having to set a token.  Be aware that if
the environment variable should be unset, the Linode CLI will stop working until
it is set again or the CLI is reconfigured with a token.

You may also use environment variables to store your Object Storage Keys for
the ``obj`` plugin that ships with the CLI.  To do so, simply set
``LINODE_CLI_OBJ_ACCESS_KEY`` and ``LINODE_CLI_OBJ_SECRET_KEY`` to the
appropriate values.  This allows using Linode Object Storage through the CLI
without having a configuration file, which is desirable in some situations.

You may also specify the path to a custom Certificate Authority file using the ``LINODE_CLI_CA``
environment variable.

If you wish to hide the API Version warning you can use the `LINODE_CLI_SUPPRESS_VERSION_WARNING`
environment variable.

Configurable API URL
^^^^^^^^^^^^^^^^^^^^

In some cases you may want to run linode-cli against a non-default Linode API URL.
This can be done using the following environment variables to override certain segments of the target API URL.

* ``LINODE_CLI_API_HOST`` - The host of the Linode API instance (e.g. ``api.linode.com``)

* ``LINODE_CLI_API_VERSION`` - The Linode API version to use (e.g. ``v4beta``)

* ``LINODE_CLI_API_SCHEME`` - The request scheme to use (e.g. ``https``)

Alternatively, these values can be configured per-user using the ``linode-cli configure`` command.

Multiple Users
^^^^^^^^^^^^^^

If you use the Linode CLI to manage multiple Linode accounts, you may configure
additional users using the ``linode-cli configure`` command.  The CLI will automatically
detect that a new user is being configured based on the token given.

Displaying Configured Users
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To see what users are configured, simply run the following::

    linode-cli show-users

The user who is currently active will be indicated by an asterisk.

Changing the Active User
^^^^^^^^^^^^^^^^^^^^^^^^

You may change the active user for all requests as follows::

    linode-cli set-user USERNAME

Subsequent CLI commands will be executed as that user by default.

Should you wish to execute a single request as a different user, you can supply
the ``--as-user`` argument to specify the username you wish to act as for that
command.  This *will not* change the active user.

Removing Configured Users
^^^^^^^^^^^^^^^^^^^^^^^^^

To remove a user from you previously configured, run::

    linode-cli remove-user USERNAME

Once a user is removed, they will need to be reconfigured if you wish to use the
CLI for them again.

.. rubric:: Next Steps

To continue to the next step of this guide, continue to the :ref:`Usage page <general_usage>`.
