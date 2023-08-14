# Usage

The Linode CLI is invoked with the `linode-cli`. There are two aliases available: `linode` and `lin`.
The CLI accepts two primary arguments, *command*  and *action*::
```bash
linode-cli <command> <action>
```

*command* is the part of the CLI you are interacting with, for example "linodes".
You can see a list of all available commands by using `--help`::
```bash
linode-cli --help
```

*action* is the action you want to perform on a given command, for example "list".
You can see a list of all available actions for a command with the `--help` for
that command::
```bash
linode-cli linodes --help
```

Some actions don't require any parameters, but many do.  To see details on how
to invoke a specific action, use `--help` for that action::
```bash
linode-cli linodes create --help
```

The first time you invoke the CLI, you will be asked to configure (see
"Configuration" below for details), and optionally select some default values
for "region," "image," and "type." If you configure these defaults, you may
omit them as parameters to actions and the default value will be used.

## Common Operations

List Linodes::
```bash
linode-cli linodes list
```

List Linodes in a Region::
```bash
linode-cli linodes list --region us-east
```

Make a Linode::
```bash
linode-cli linodes create --type g5-standard-2 --region us-east --image linode/debian9 --label cli-1 --root_pass
```

Make a Linode using Default Settings::
```bash
linode-cli linodes create --label cli-2 --root_pass
```

Reboot a Linode::
```bash
linode-cli linodes reboot 12345
```

View available Linode types::
```bash
linode-cli linodes types
```

View your Volumes::
```bash
linode-cli volumes list
```

View your Domains::
```bash
linode-cli domains list
```

View records for a single Domain::
```bash
linode-cli domains records-list 12345
```

View your user::
```bash
linode-cli profile view
```

## Specifying List Arguments

When running certain commands, you may need to specify multiple values for a list
argument. This can be done by specifying the argument multiple times for each
value in the list. For example, to create a Linode with multiple `tags`
you can execute the following::
```bash
linode-cli linodes create --region us-east --type g6-nanode-1 --tags tag1 --tags tag2
```

Lists consisting of nested structures can also be expressed through the command line.
For example, to create a Linode with a public interface on `eth0` and a VLAN interface
on `eth1` you can execute the following::
```bash
linode-cli linodes create \
    --region us-east --type g6-nanode-1 --image linode/ubuntu22.04 \
    --root_pass "myr00tp4ss123" \
    --interfaces.purpose public \
    --interfaces.purpose vlan --interfaces.label my-vlan
```

## Specifying Nested Arguments

When running certain commands, you may need to specify an argument that is nested
in another field. These arguments can be specified using a `.` delimited path to
the argument. For example, to create a firewall with an inbound policy of `DROP`
and an outbound policy of `ACCEPT`, you can execute the following::
```bash
linode-cli firewalls create --label example-firewall --rules.outbound_policy ACCEPT --rules.inbound_policy DROP
```

## Suppressing Defaults

If you configured default values for `image`, `authorized_users`, `region`,
database `engine`, and Linode `type`, they will be sent for all requests that accept them
if you do not specify a different value.  If you want to send a request *without* these
arguments, you must invoke the CLI with the `--no-defaults` option.

For example, to create a Linode with no `image` after a default Image has been
configured, you would do this::
```bash
linode-cli linodes create --region us-east --type g5-standard-2 --no-defaults
```

## Suppressing Warnings

In some situations, like when the CLI is out of date, it will generate a warning
in addition to its normal output.  If these warnings can interfere with your
scripts or you otherwise want them disabled, simply add the `--suppress-warnings`
flag to prevent them from being emitted.

## Shell Completion

To generate a completion file for a given shell type, use the `completion` command;
for example to generate completions for bash run::
```bash
linode-cli completion bash
```

The output of this command is suitable to be included in the relevant completion
files to enable command completion on your shell.

This command currently supports completions bash and fish shells.

Use `bashcompinit` on zsh with the bash completions for support on zsh shells.
