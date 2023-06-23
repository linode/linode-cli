linode-cli
==========

The Linode Command Line Interface

.. image:: https://raw.githubusercontent.com/linode/linode-cli/main/demo.gif

Installation
------------

From pypi::

   pip3 install linode-cli

From source::

   git clone git@github.com:linode/linode-cli.git
   cd linode-cli
   make install

This will need to be repeated on each pull.  For a build to succeed, see
`Building from Source`_ below.

.. _Building from Source: #building-from-source

Docker Hub
^^^^^^^^^^

The Linode CLI can also be downloaded and run using the image available on `Docker Hub`_.

.. _Docker Hub: https://hub.docker.com/r/linode/cli

Using a Linode API Token::

    docker run --rm -it -e LINODE_CLI_TOKEN=$LINODE_TOKEN linode/cli:latest linodes list

Using an existing config file::

    docker run --rm -it -v $HOME/.config/linode-cli:/home/cli/.config/linode-cli linode/cli:latest linodes list

GitHub Actions
^^^^^^^^^^^^^^

The Linode CLI can be automatically installed and authenticated in a GitHub actions environment using
the `Setup Linode CLI`_ GitHub Action::

     - name: Install the Linode CLI
       uses: linode/action-linode-cli@v1
       with:
         token: ${{ secrets.LINODE_TOKEN }}

.. _Setup Linode CLI: https://github.com/marketplace/actions/setup-linode-cli

Upgrading
---------

To upgrade to the latest version of the Linode CLI::

   pip3 install linode-cli --upgrade

Community Distributions
-----------------------

The Linode CLI is also available through the following unofficial channels thanks
to our awesome community!  Please note that these distributions are not included
in our release testing.

Homebrew
^^^^^^^^

Installation::

   brew install linode-cli

Upgrading::

   brew upgrade linode-cli

Usage
-----

The Linode CLI is invoked with the `linode-cli`. There are two aliases available: `linode` and `lin`.
The CLI accepts two primary arguments, *command*  and *action*::

   linode-cli <command> <action>

*command* is the part of the CLI you are interacting with, for example "linodes".
You can see a list of all available commands by using `--help`::

   linode-cli --help

*action* is the action you want to perform on a given command, for example "list".
You can see a list of all available actions for a command with the `--help` for
that command::

   linode-cli linodes --help

Some actions don't require any parameters, but many do.  To see details on how
to invoke a specific action, use `--help` for that action::

   linode-cli linodes create --help

The first time you invoke the CLI, you will be asked to configure (see
"Configuration" below for details), and optionally select some default values
for "region," "image," and "type." If you configure these defaults, you may
omit them as parameters to actions and the default value will be used.

Common Operations
^^^^^^^^^^^^^^^^^

List Linodes::

   linode-cli linodes list

List Linodes in a Region::

   linode-cli linodes list --region us-east

Make a Linode::

   linode-cli linodes create --type g5-standard-2 --region us-east --image linode/debian9 --label cli-1 --root_pass

Make a Linode using Default Settings::

   linode-cli linodes create --label cli-2 --root_pass

Reboot a Linode::

   linode-cli linodes reboot 12345

View available Linode types::

   linode-cli linodes types

View your Volumes::

   linode-cli volumes list

View your Domains::

   linode-cli domains list

View records for a single Domain::

   linode-cli domains records-list 12345

View your user::

   linode-cli profile view

Configuration
"""""""""""""

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

Specifying List Arguments
"""""""""""""""""""""""""

When running certain commands, you may need to specify multiple values for a list
argument. This can be done by specifying the argument multiple times for each
value in the list. For example, to create a Linode with multiple ``tags``
you can execute the following::

    linode-cli linodes create --region us-east --type g6-nanode-1 --tags tag1 --tags tag2

Lists consisting of nested structures can also be expressed through the command line.
For example, to create a Linode with a public interface on ``eth0`` and a VLAN interface
on ``eth1`` you can execute the following::

    linode-cli linodes create \
        --region us-east --type g6-nanode-1 --image linode/ubuntu22.04 \
        --root_pass "myr00tp4ss123" \
        --interfaces.purpose public \
        --interfaces.purpose vlan --interfaces.label my-vlan

Specifying Nested Arguments
"""""""""""""""""""""""""""

When running certain commands, you may need to specify an argument that is nested
in another field. These arguments can be specified using a ``.`` delimited path to
the argument. For example, to create a firewall with an inbound policy of ``DROP``
and an outbound policy of ``ACCEPT``, you can execute the following::

    linode-cli firewalls create --label example-firewall --rules.outbound_policy ACCEPT --rules.inbound_policy DROP

Suppressing Defaults
""""""""""""""""""""

If you configured default values for ``image``, ``authorized_users``, ``region``,
database ``engine``, and Linode ``type``, they will be sent for all requests that accept them
if you do not specify a different value.  If you want to send a request *without* these
arguments, you must invoke the CLI with the ``--no-defaults`` option.

For example, to create a Linode with no ``image`` after a default Image has been
configured, you would do this::

   linode-cli linodes create --region us-east --type g5-standard-2 --no-defaults

Suppressing Warnings
""""""""""""""""""""

In some situations, like when the CLI is out of date, it will generate a warning
in addition to its normal output.  If these warnings can interfere with your
scripts or you otherwise want them disabled, simply add the ``--suppress-warnings``
flag to prevent them from being emitted.

Shell Completion
""""""""""""""""

To generate a completion file for a given shell type, use the ``completion`` command;
for example to generate completions for bash run::

   linode-cli completion bash

The output of this command is suitable to be included in the relevant completion
files to enable command completion on your shell.

This command currently supports completions bash and fish shells.

Use ``bashcompinit`` on zsh with the bash completions for support on zsh shells.

Environment Variables
"""""""""""""""""""""

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

Configurable API URL
""""""""""""""""""""

In some cases you may want to run linode-cli against a non-default Linode API URL.
This can be done using the following environment variables to override certain segments of the target API URL.

* ``LINODE_CLI_API_HOST`` - The host of the Linode API instance (e.g. ``api.linode.com``)

* ``LINODE_CLI_API_VERSION`` - The Linode API version to use (e.g. ``v4beta``)

* ``LINODE_CLI_API_SCHEME`` - The request scheme to use (e.g. ``https``)

Multiple Users
^^^^^^^^^^^^^^

If you use the Linode CLI to manage multiple Linode accounts, you may configure
additional users using the ``linode-cli configure`` command.  The CLI will automatically
detect that a new user is being configured based on the token given.

Displaying Configured Users
"""""""""""""""""""""""""""

To see what users are configured, simply run the following::

   linode-cli show-users

The user who is currently active will be indicated by an asterisk.

Changing the Active User
""""""""""""""""""""""""

You may change the active user for all requests as follows::

   linode-cli set-user USERNAME

Subsequent CLI commands will be executed as that user by default.

Should you wish to execute a single request as a different user, you can supply
the ``--as-user`` argument to specify the username you wish to act as for that
command.  This *will not* change the active user.

Removing Configured Users
"""""""""""""""""""""""""

To remove a user from you previously configured, run::

   linode-cli remove-user USERNAME

Once a user is removed, they will need to be reconfigured if you wish to use the
CLI for them again.

Customizing Output
------------------

Changing Output Fields
^^^^^^^^^^^^^^^^^^^^^^

By default, the CLI displays on some pre-selected fields for a given type of
response.  If you want to see everything, just ask::

   linode-cli linodes list --all

Using `--all` will cause the CLI to display all returned columns of output.
Note that this will probably be hard to read on normal-sized screens for most
actions.

If you want even finer control over your output, you can request specific columns
be displayed::

   linode-cli linodes list --format 'id,region,status,disk,memory,vcpus,transfer'

This will show some identifying information about your Linode as well as the
resources it has access to.  Some of these fields would be hidden by default -
that's ok.  If you ask for a field, it'll be displayed.

Output Formatting
^^^^^^^^^^^^^^^^^

While the CLI by default outputs human-readable tables of data, you can use the
CLI to generate output that is easier to process.

Machine Readable Output
"""""""""""""""""""""""

To get more machine-readable output, simply request it::

   linode-cli linodes list --text

If a tab is a bad delimiter, you can configure that as well::

  linode-cli linodes list --text --delimiter ';'

You may also disable header rows (in any output format)::

   linode-cli linodes list --no-headers --text

JSON Output
"""""""""""

To get JSON output from the CLI, simple request it::

   linode-cli linodes list --json --all

While the `--all` is optional, you probably want to see all output fields in
your JSON output.  If you want your JSON pretty-printed, we can do that too::

   linode-cli linodes list --json --pretty --all

Plugins
-------

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
^^^^^^^^^^^^^^^^^^

For information on how To write your own Third Party Plugin, see the `Plugins documentation`_.

.. _Plugins documentation: https://github.com/linode/linode-cli/blob/main/linodecli/plugins/README.md

Building from Source
--------------------

In order to successfully build the CLI, your system will require the following:

 * The ``make`` command
 * ``python3``
 * ``pip3`` (to install ``requirements.txt``)

Before attempting a build, install python dependencies like this::

   make requirements

Once everything is set up, you can initiate a build like so::

    make build

If desired, you may pass in ``SPEC=/path/to/openapi-spec`` when running ``build``
or ``install``.  This can be a URL or a path to a local spec, and that spec will
be used when generating the CLI.  A yaml or json file is accepted.

To install the package as part of the build process, use this command::

   make install

Testing
-------

**WARNING!** Running the CLI tests will remove all linodes and data associated
with the account. It is only recommended to run these tests if you are an advanced
user.

Running the Tests
^^^^^^^^^^^^^^^^^

Running the tests locally is simple. The only requirements are that you export Linode API token as LINODE_CLI_TOKEN::

   export LINODE_CLI_TOKEN="your_token"



More information on Managing Linode API tokens can be found here - https://www.linode.com/docs/products/tools/api/guides/manage-api-tokens/

In order to run the full integration test, run::

    make testint

To run specific test package, use environment variable `INTEGRATION_TEST_PATH` with `testint` command::

   make INTEGRATION_TEST_PATH="cli" testint



Lastly, to run specific test case, use environment variables `TEST_CASE` with `testint` command::

   make TEST_CASE=test_help_page_for_non_aliased_actions testint


Contributing
------------

This CLI is generated based on the OpenAPI specification for Linode's API.  As
such, many changes are made directly to the spec.

Please follow the `Contributing Guidelines`_ when making a contribution.

.. _Contributing Guidelines: https://github.com/linode/linode-cli/blob/main/CONTRIBUTING.md

Specification Extensions
^^^^^^^^^^^^^^^^^^^^^^^^

In order to be more useful, the following `Specification Extensions`_ have been
added to Linode's OpenAPI spec:

+-----------------------------+-------------+-------------------------------------------------------------------------------------------+
|Attribute                    | Location    | Purpose                                                                                   |
+-----------------------------+-------------+-------------------------------------------------------------------------------------------+
|x-linode-cli-action          | method      | The action name for operations under this path. If not present, operationId is used.      |
+-----------------------------+-------------+-------------------------------------------------------------------------------------------+
|x-linode-cli-color           | property    | If present, defines key-value pairs of property value: color.  Colors must be one of      |
|                             |             | "red", "green", "yellow", "white", and "black".  Must include a default.                  |
+-----------------------------+-------------+-------------------------------------------------------------------------------------------+
|x-linode-cli-command         | path        | The command name for operations under this path. If not present, "default" is used.       |
+-----------------------------+-------------+-------------------------------------------------------------------------------------------+
|x-linode-cli-display         | property    | If truthy, displays this as a column in output.  If a number, determines the ordering     |
|                             |             | (left to right).                                                                          |
+-----------------------------+-------------+-------------------------------------------------------------------------------------------+
|x-linode-cli-format          | property    | Overrides the "format" given in this property for the CLI only.  Valid values are `file`  |
|                             |             | and `json`.                                                                               |
+-----------------------------+-------------+-------------------------------------------------------------------------------------------+
|x-linode-cli-skip            | path        | If present and truthy, this method will not be available in the CLI.                      |
+-----------------------------+-------------+-------------------------------------------------------------------------------------------+
+x-linode-cli-allowed-defaults| requestBody | Tells the CLI what configured defaults apply to this request. Valid defaults are "region",|
+                             |             | "image", "authorized_users", "engine", and "type".                                        |
+-----------------------------+-------------+-------------------------------------------------------------------------------------------+
+x-linode-cli-nested-list     | content-type| Tells the CLI to flatten a single object into multiple table rows based on the keys       |
|                             |             | included in this value.  Values should be comma-delimited JSON paths, and must all be     |
|                             |             | present on response objects.                                                              |
|                             |             |                                                                                           |
|                             |             | When used, a new key ``_split`` is added to each flattened object whose value is the last |
|                             |             | segment of the JSON path used to generate the flattened object from the source.           |
+-----------------------------+-------------+-------------------------------------------------------------------------------------------+
|x-linode-cli-use-schema      | content-type| Overrides the normal schema for the object and uses this instead.  Especially useful when |
|                             |             | paired with ``x-linode-cli-nested-list``, allowing a schema to describe the flattened     |
|                             |             | object instead of the original object.                                                    |
+-----------------------------+-------------+-------------------------------------------------------------------------------------------+

.. _Specification Extensions: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.1.md#specificationExtensions
