linode-cli
==========

The Linode Command Line Interface

.. image:: https://raw.githubusercontent.com/linode/linode-cli/master/demo.gif

Installation
------------

From pypi::

   pip install linode-cli

From source::

   git clone git@github.com:linode/linode-cli.git
   cd linode-cli
   make install SPEC=https://developers.linode.com/openapi.yaml

This will need to be repeated on each pull.  For a build to succeed, see
`Building from Source`_ below.

.. _Building from Source: #building-from-source

Usage
-----

The Linode CLI is invoked with the `linode-cli`.  The CLI accepts two primary
arguments, *command*  and *action*::

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

The first time you invoke the CLI, you will be asked to configure it with a
token, and optionally select some default values for "region," "image," and "type."
If you configure these defaults, you may omit them as parameters to actions
and the default value will be used.

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

Reconfiguring
"""""""""""""

If your token expires or you want to otherwise change your configuration, simply
run the *configure* command::

   linode-cli configure

Suppressing Defaults
""""""""""""""""""""

If you configured default values for `image`, `region`, and Linode `type`, they
will be sent for all requests that accept them if you do not specify a different
value.  If you want to send a request *without* these arguments, you must invoke
the CLI with the `--no-defaults` option.  For example, to create a Linode with
no `image` after a default Image has been configured, you would do this::

   linode-cli linodes create --region us-east --type g5-standard-2 --no-defaults

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

Building from Source
--------------------

In order to successfully build the CLI, your system will require the following:

 * The ``make`` command
 * ``python`` and ``python3`` (both versions are required to build a package)
 * ``pip`` and ``pip3`` (to install ``requirements.txt`` for both python versions)

Before attempting a build, install python dependencies like this::

   make requirements

Once everything is set up, you can initiate a build like so::

    make build SPEC=https://developers.linode.com/openapi.yaml

In this example, ``SPEC`` is being set to the public URL of Linode's OpenAPI
specification.  This can be replaced with a local version of the spec, and the
URL replaces with a path to the spec file, if desired.

To install the package as part of the build process, use this command::

   make install SPEC=https://developers.linode.com/openapi.yaml PYTHON=3

When using ``install``, the ``PYCMD`` argument is optional - if provided, it
will install the CLI for that version of python.  Valid values are ``2`` and
``3``, and it will default to ``3``.

Testing 
-------

WARNING! Running the CLI tests will remove all linodes and data associated
with the account. It is only recommended to run these tests if you are an advanced
user.

Installation
^^^^^^^^^^^^

The CLI uses the Bash Automated Testing System (BATS) for testing. To install run the following:

OSX users::

   brew install bats-core

Installing Bats from source::

   Check out a copy of the Bats repository. Then, either add the Bats bin directory to your $PATH, or run the provided install.sh command with the location to the prefix in which you want to install Bats. For example, to install Bats into /usr/local,

   git clone https://github.com/bats-core/bats-core.git
   cd bats-core
   ./install.sh /usr/local

Running the Tests
^^^^^^^^^^^^^^^^^

Running the tests is simple. The only requirement is that you have a .linode-cli in your user folder containing your test user token::

   bats test/**


Contributing
------------

This CLI is generated based on the OpenAPI specification for Linode's API.  As
such, many changes are made directly to the spec.

Specification Extensions
^^^^^^^^^^^^^^^^^^^^^^^^

In order to be more useful, the following `Specification Extensions`_ have been
added to Linode's OpenAPI spec:

+---------------------+----------+-------------------------------------------------------------------------------------------+
|Attribute            | Location | Purpose                                                                                   |
+---------------------+----------+-------------------------------------------------------------------------------------------+
|x-linode-cli-display | property | If truthy, displays this as a column in output.  If a number, determines the ordering     |
|                     |          | (left to right).                                                                          |
+---------------------+----------+-------------------------------------------------------------------------------------------+
|x-linode-cli-command | path     | The command name for operations under this path. If not present, "default" is used.       |
+---------------------+----------+-------------------------------------------------------------------------------------------+
|x-linode-cli-action  | method   | The action name for operations under this path. If not present, operationId is used.      |
+---------------------+----------+-------------------------------------------------------------------------------------------+
|x-linode-cli-color   | property | If present, defines key-value pairs of property value: color.  Colors must be understood  |
|                     |          | by colorclass.Color.  Must include a default_                                             |
+---------------------+----------+-------------------------------------------------------------------------------------------+
|x-linode-cli-skip    | path     | If present and truthy, this method will not be available in the CLI.                      |
+---------------------+----------+-------------------------------------------------------------------------------------------+

.. _Specification Extensions: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#specificationExtensions
