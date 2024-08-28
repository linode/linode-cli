.. _general_usage:

Usage
=====

The Linode CLI is invoked with the :code:`linode-cli`,
or with either of its two aliases available: :code:`linode` and :code:`lin`.

The CLI accepts two primary arguments, *command*  and *action*::

    linode-cli <command> <action>

*command* is the part of the CLI you are interacting with, for example "linodes".
You can see a list of all available commands by using :code:`--help`::

    linode-cli --help


*action* is the action you want to perform on a given command, for example "list".
You can see a list of all available actions for a command with the :code:`--help` for
that command::

    linode-cli linodes --help

Some actions don't require any parameters, but many do.  To see details on how
to invoke a specific action, use :code:`--help` for that action::

    linode-cli linodes create --help

The first time you invoke the CLI, you will be asked to configure (see
"Configuration" below for details), and optionally select some default values
for "region," "image," and "type." If you configure these defaults, you may
omit them as parameters to actions and the default value will be used.

Common Operations
-----------------

List Linodes::

    linode-cli linodes list

List Linodes in a Region::

    linode-cli linodes list --region us-east

Create a Linode::

    linode-cli linodes create --type g5-standard-2 --region us-east --image linode/debian9 --label cli-1 --root_pass

Create a Linode using default settings::

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

Specifying List Arguments
-------------------------

When running certain commands, you may need to specify multiple values for a list
argument. This can be done by specifying the argument multiple times for each
value in the list. For example, to create a Linode with multiple :code:`tags`
you can execute the following::

    linode-cli linodes create --region us-east --type g6-nanode-1 --tags tag1 --tags tag2

Lists consisting of nested structures can also be expressed through the command line.
Duplicated attribute will signal a different object.
For example, to create a Linode with a public interface on :code:`eth0` and a VLAN interface
on :code:`eth1` you can execute the following::

    linode-cli linodes create \
        --region us-east --type g6-nanode-1 --image linode/ubuntu22.04 \
        --root_pass "myr00tp4ss123" \
        # The first interface (index 0) is defined with the public purpose
        --interfaces.purpose public \
        # The second interface (index 1) is defined with the vlan purpose. 
        # The duplicate `interfaces.purpose` here tells the CLI to start building a new interface object.
        --interfaces.purpose vlan --interfaces.label my-vlan

Specifying Nested Arguments
---------------------------

When running certain commands, you may need to specify an argument that is nested
in another field. These arguments can be specified using a :code:`.` delimited path to
the argument. For example, to create a firewall with an inbound policy of :code:`DROP`
and an outbound policy of :code:`ACCEPT`, you can execute the following::

    linode-cli firewalls create --label example-firewall --rules.outbound_policy ACCEPT --rules.inbound_policy DROP

Special Arguments
-----------------

In some cases, certain values for arguments may have unique functionality.

Null Values
^^^^^^^^^^^

Arguments marked as nullable can be passed the value :code:`null` to send an explicit null value to the Linode API::

    linode-cli networking ip-update --rdns null 127.0.0.1

Empty Lists
^^^^^^^^^^^

List arguments can be passed the value :code:`[]` to send an explicit empty list value to the Linode API::

    linode-cli networking ip-share --linode_id 12345 --ips []

Suppressing Defaults
--------------------

If you configured default values for :code:`image`, :code:`authorized_users`, :code:`region`,
database :code:`engine`, and Linode :code:`type`, they will be sent for all requests that accept them
if you do not specify a different value.  If you want to send a request *without* these
arguments, you must invoke the CLI with the :code:`--no-defaults` option.

For example, to create a Linode with no :code:`image` after a default Image has been
configured, you would do this::

    linode-cli linodes create --region us-east --type g5-standard-2 --no-defaults

Suppressing Warnings
--------------------

In some situations, like when the CLI is out of date, it will generate a warning
in addition to its normal output.  If these warnings can interfere with your
scripts or you otherwise want them disabled, simply add the :code:`--suppress-warnings`
flag to prevent them from being emitted.

## Suppressing Retries

Sometimes the API responds with a error that can be ignored. For example a timeout
or nginx response that can't be parsed correctly, by default the CLI will retry
calls on these errors we've identified. If you'd like to disable this behavior for
any reason use the :code:`--no-retry` flag.

Shell Completion
----------------

To generate a completion file for a given shell type, use the :code:`completion` command;
for example to generate completions for bash run::

    linode-cli completion bash

The output of this command is suitable to be included in the relevant completion
files to enable command completion on your shell.

This command currently supports completions bash and fish shells.

Use :code:`bashcompinit` on zsh with the bash completions for support on zsh shells.

.. rubric:: Next Steps

To continue to the next step of this guide, continue to the :ref:`Output page <general_output>`.
