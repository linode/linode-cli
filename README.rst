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
   make install

This will need to be repeated on each pull.  For a build to succeed, see
`Building from Source`_ below.

.. _Building from Source: #building-from-source

Upgrading
---------

To upgrade to the latest version of the Linode CLI::

   pip install linode-cli --upgrade

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

If you configured default values for ``image``, ``region``, and Linode ``type``, they
will be sent for all requests that accept them if you do not specify a different
value.  If you want to send a request *without* these arguments, you must invoke
the CLI with the ``--no-defaults`` option.  For example, to create a Linode with
no ``image`` after a default Image has been configured, you would do this::

   linode-cli linodes create --region us-east --type g5-standard-2 --no-defaults

Suppressing Warnings
""""""""""""""""""""

In some situations, like when the CLI is out of date, it will generate a warning
in addition to its normal output.  If these warnings can interfere with your
scripts or you otherwise want them disabled, simply add the ``--suppress-warnings``
flag to prevent them from being emitted.

Environment Variables
"""""""""""""""""""""

If you prefer, you may store your token in an environment variable named
``LINODE_CLI_TOKEN`` instead of using the configuration file.  Doing so allows you
to bypass the initial configuration, and subsequent calls to ``linode-cli configure``
will allow you to set defaults without having to set a token.  Be aware that if
the environment variable should be unset, the Linode CLI will stop working until
it is set again or the CLI is reconfigured with a token.

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

Kubernetes Deployment Plugin
----------------------------

A plugin is included that allows you to deploy a Kubernetes cluster on Linode! These commands require Terraform, the Kubernetes CLI, and an SSH key added to your ssh-agent. If any dependencies are not present, you'll recieve installation instructions during command execution.

This Kubernetes cluster is integrated with Linode in a number of ways:

* When you deploy a LoadBalancer-type service through Kubernetes a Linode
  NodeBalancer will be automatically created and managed for the Pods backing
  that service. (`Linode Cloud Controller Manager`_)
* When PersistentVolumes are created through Kubernetes, those volumes will be
  Linode Block Storage volumes. These are also automatically managed with the
  lifecycle of the PersistentVolume resource. (`Linode Container Storage
  Interface`_)
* Nodes in Kubernetes have the appropriate Linode InternalIP, ExternalIP and
  ProviderID fields, meaning that CNI and other controllers can take advantage
  of these fields for the sake of NetworkPolicy and other Kubernetes features.
* Nodes in Kubernetes are labeled with the Linode Region and Linode Type, which
  can also be used by controllers for the purposes of scheduling
* The Kubernetes metrics-server is installed, allowing you to use ``kubectl top``

The following is the help message for the command::

   $ linode-cli k8s-alpha create --help
   usage: k8s-alpha create [-h] [--node-type TYPE] [--nodes COUNT]
                           [--master-type TYPE] [--region REGION]
                           [--ssh-public-key KEYPATH]
                           NAME

   positional arguments:
     NAME                  A name for the cluster.

   optional arguments:
     -h, --help            show this help message and exit
     --node-type TYPE      The Linode Type ID for cluster Nodes as retrieved with
                           `linode-cli linodes types`. (default "g6-standard-2")
     --nodes COUNT         The number of Linodes to deploy as Nodes in the
                           cluster. (default 3)
     --master-type TYPE    The Linode Type ID for cluster Master Nodes as
                           retrieved with `linode-cli linodes types`. (default
                           "g6-standard-2")
     --region REGION       The Linode Region ID in which to deploy the cluster as
                           retrieved with `linode-cli regions list`. (default
                           is whatever you set during CLI configuration)
     --ssh-public-key KEYPATH
                           The path to your public key file which will be used to
                           access Nodes during initial provisioning only! If you don't
                           use id_rsa as your private key name, use the flag
                           --ssh-public-key and supply your public key path. If
                           you use id_rsa as your key name and it's been added
                           to your ssh-agent, omit the flag.
                           (default $HOME/.ssh/id_rsa.pub).

Here's an example usage of the command, creating a cluster with six 2GB Linodes as
the Nodes::

   linode-cli k8s-alpha create mycluster77 --node-type g6-standard-1 --nodes 6 --master-type g6-standard-4 --region us-east --ssh-public-key $HOME/.ssh/id_rsa.pub

Once you have created a cluster, that cluster's kubeconfig is automatically merged into
your default kubeconfig. The kubectl context is also switched so that you can immediately begin
interacting with the cluster. For example::

   kubectl get pods --all-namespaces
   kubectl create -f the-next-big-social-app-manifest.yaml

If you have any questions, or just want to hang out, visit us on #linode on the `Kubernetes official Slack`_!

.. _Kubernetes official Slack: http://slack.k8s.io/
.. _Linode Cloud Controller Manager: https://github.com/linode/linode-cloud-controller-manager
.. _Linode Container Storage Interface: https://github.com/linode/linode-blockstorage-csi-driver

To delete a cluster simply run::

   linode-cli k8s-alpha delete mycluster77

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

.. _Plugins documentation: https://github.com/linode/linode-cli/blob/master/linodecli/plugins/README.md

Building from Source
--------------------

In order to successfully build the CLI, your system will require the following:

 * The ``make`` command
 * ``python`` and ``python3`` (both versions are required to build a package)
 * ``pip`` and ``pip3`` (to install ``requirements.txt`` for both python versions)

Before attempting a build, install python dependencies like this::

   make requirements

Once everything is set up, you can initiate a build like so::

    make build

If desired, you may pass in ``SPEC=/path/to/openapi-spec`` when running ``build``
or ``install``.  This can be a URL or a path to a local spec, and that spec will
be used when generating the CLI.  A yaml or json file is accepted.

To install the package as part of the build process, use this command::

   make install PYTHON=3

When using ``install``, the ``PYTHON`` argument is optional - if provided, it
will install the CLI for that version of python.  Valid values are ``2`` and
``3``, and it will default to ``3``.

Testing
-------

**WARNING!** Running the CLI tests will remove all linodes and data associated
with the account. It is only recommended to run these tests if you are an advanced
user.

Installation
^^^^^^^^^^^^

The CLI uses the Bash Automated Testing System (BATS) for testing. To install run the following:

**OSX users**::

   brew install bats-core

**Installing Bats from source**

Check out a copy of the Bats repository. Then, either add the Bats bin directory to your
$PATH, or run the provided install.sh command with the location to the prefix in which you
want to install Bats. For example, to install Bats into /usr/local::

   git clone https://github.com/bats-core/bats-core.git
   cd bats-core
   ./install.sh /usr/local

Running the Tests
^^^^^^^^^^^^^^^^^

Running the tests is simple. The only requirements are that you have a .linode-cli in your user folder containing your test user token::

   ./test/test-runner.sh

**Running Tests via Docker**

The openapi spec must first be saved to the base of the linode-cli project:

   curl -o ./openapi.yaml https://developers.linode.com/api/docs/v4/openapi.yaml

Run the following command to build the tests container:

   docker build -f Dockerfile-bats -t linode-cli-tests .

Run the following command to run the test

   docker run -e TOKEN_1=$INSERT_YOUR_TOKEN_HERE -e TOKEN_2=$INSERT_YOUR_TOKEN_HERE --rm linode-cli-tests

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
|                     |          | by colorclass.Color.  Must include a default.                                             |
+---------------------+----------+-------------------------------------------------------------------------------------------+
|x-linode-cli-skip    | path     | If present and truthy, this method will not be available in the CLI.                      |
+---------------------+----------+-------------------------------------------------------------------------------------------+

.. _Specification Extensions: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.1.md#specificationExtensions
