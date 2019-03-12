#!/usr/local/bin/python3
from __future__ import print_function

import argparse
import os
import pkg_resources
from sys import argv, exit

import requests
import yaml
from terminaltables import SingleTable

from .cli import CLI
from .response import ModelAttr, ResponseModel
from .operation import CLIArg, CLIOperation, URLParam
from .output import OutputMode
from linodecli import plugins


# this might not be installed at the time of building
try:
    VERSION = pkg_resources.require("linode-cli")[0].version
except:
    VERSION = 'building'
BASE_URL = 'https://api.linode.com/v4'


cli = CLI(VERSION, BASE_URL, skip_config='--skip-config' in argv)

def main():
    ## Command Handling
    parser = argparse.ArgumentParser("linode-cli", add_help=False)
    parser.add_argument('command', metavar='COMMAND', nargs='?', type=str,
                        help="The command to invoke in the CLI.")
    parser.add_argument('action', metavar='ACTION', nargs='?', type=str,
                        help="The action to perform in this command.")
    parser.add_argument('--help', action="store_true",
                        help="Display information about a command, action, or "
                             "the CLI overall.")
    parser.add_argument('--text', action="store_true",
                        help="Display text output with a delimiter (defaults to tabs).")
    parser.add_argument('--delimiter', metavar='DELIMITER', type=str,
                        help="The delimiter when displaying raw output.")
    parser.add_argument('--json', action='store_true',
                        help="Display output as JSON")
    parser.add_argument('--markdown', action='store_true',
                        help="Display output in Markdown format.")
    parser.add_argument('--pretty', action='store_true',
                        help="If set, pretty-print JSON output")
    parser.add_argument('--no-headers', action='store_true',
                        help="If set, does not display headers in output.")
    parser.add_argument('--page', metavar='PAGE', type=int, default=1,
                        help="For listing actions, specifies the page to request")
    parser.add_argument('--all', action='store_true',
                        help="If set, displays all possible columns instead of "
                             "the default columns.  This may not work well on "
                             "some terminals.")
    parser.add_argument('--format', metavar='FORMAT', type=str,
                        help="The columns to display in output.  Provide a comma-"
                             "separated list of column names.")
    parser.add_argument('--no-defaults', action='store_true',
                        help="Suppress default values for arguments.  Default values "
                             "are configured on initial setup or with linode-cli configure")
    parser.add_argument('--as-user', metavar='USERNAME', type=str,
                        help="The username to execute this command as.  This user must "
                             "be configured.")
    parser.add_argument('--suppress-warnings', action='store_true',
                        help="Suppress warnings that are intended for human users. "
                             "This is useful for scripting the CLI's behavior.")
    parser.add_argument('--version', '-v', action="store_true",
                        help="Prints version information and exits.")

    parsed, args = parser.parse_known_args()

    # setup cli class
    if parsed.text:
        cli.output_handler.mode = OutputMode.delimited
    elif parsed.json:
        cli.output_handler.mode = OutputMode.json
    elif parsed.markdown:
        cli.output_handler.mode = OutputMode.markdown
    if parsed.delimiter:
        cli.output_handler.delimiter = parsed.delimiter
    if parsed.pretty:
        cli.output_handler.pretty_json = True
    if parsed.no_headers:
        cli.output_handler.headers = False
    if parsed.all:
        cli.output_handler.columns = '*'
    elif parsed.format:
        cli.output_handler.columns = parsed.format

    cli.defaults = not parsed.no_defaults
    cli.suppress_warnings = parsed.suppress_warnings
    cli.page = parsed.page

    if parsed.as_user:
        # if they are acting as a non-default user, set it up early
        cli.config.set_user(parsed.as_user)

    if parsed.version:
        # print version info and exit
        print("linode-cli {}".format(VERSION))
        print("Built off spec version {}".format(cli.spec_version))
        exit(0)

    # handle a bake - this is used to parse a spec and bake it as a pickle
    if parsed.command == "bake":
        if parsed.action is None:
            print("No spec provided, cannot bake")
            exit(9)
        print("Baking...")
        spec_loc = parsed.action
        try:
            if os.path.exists(os.path.expanduser(spec_loc)):
                with open(os.path.expanduser(spec_loc)) as f:
                    spec = yaml.safe_load(f.read())
            else: # try to GET it
                resp = requests.get(spec_loc)
                if resp.status_code == 200:
                    spec = yaml.safe_load(resp.content)
                else:
                    raise RuntimeError("Request failed to {}".format(spec_loc))
        except Exception as e:
            print("Could not load spec: {}".format(e))
            exit(2)

        cli.bake(spec)
        print("Baking bash completions...")
        # this step would normally happen on laod
        if '_base_url' in cli.ops:
            del cli.ops['_base_url']
        if '_spec_version' in cli.ops:
            del cli.ops['_spec_version']
        # do the baking
        cli.bake_completions()
        print("Done.")
        exit(0)
    elif cli.ops is None:
        # if not spec was found and we weren't baking, we're doomed
        exit(3)


    # handle a help for the CLI
    if parsed.command is None or (parsed.command is None and  parsed.help):
        parser.print_help()

        # commands to manager CLI users (don't call out to API)
        print()
        print('CLI user management commands:')
        um_commands = [['configure', 'set-user', 'show-users'],['remove-user']]
        table = SingleTable(um_commands)
        table.inner_heading_row_border = False
        print(table.table)

        # commands generated from the spec (call the API directly)
        print()
        print("Available commands:")

        content = [c for c in cli.ops.keys()]
        proc = []
        for i in range(0,len(content),3):
            proc.append(content[i:i+3])
        if content[i+3:]:
            proc.append(content[i+3:])

        table = SingleTable(proc)
        table.inner_heading_row_border = False
        print(table.table)

        # plugins registered to the CLI (do arbitrary things)
        if plugins.available:
            # only show this if there are any available plugins
            print("Available plugins:")

            plugin_content = [p for p in plugins.available]
            plugin_proc = []

            for i in range(0,len(plugin_content),3):
                plugin_proc.append(plugin_content[i:i+3])
            if plugin_content[i+3:]:
                plugin_proc.append(plugin_content[i+3:])

            plugin_table = SingleTable(plugin_proc)
            plugin_table.inner_heading_row_border = False

            print(plugin_table.table)

        print()
        print("To reconfigure, call `linode-cli configure`")
        print("For comprehensive documentation, visit https://developers.linode.com")
        exit(0)


    # configure
    if parsed.command == "configure":
        if parsed.help:
            print('linode-cli configure')
            print()
            print('Configured the Linode CLI.  This command can be used to change')
            print('defaults selected for the current user, or to configure additional')
            print('users.')
            exit(0)
        else:
            cli.configure()
            exit(0)

    # block of commands for user-focused operations
    if parsed.command == "set-user":
        if parsed.help or not parsed.action:
            print('linode-cli set-user [USER]')
            print()
            print('Sets the active user for the CLI out of users you have configured.')
            print('To configure a new user, see `linode-cli configure`')
            exit(0)
        else:
            cli.config.set_default_user(parsed.action)
            exit(0)

    if parsed.command == "show-users":
        if parsed.help:
            print('linode-cli show-users')
            print()
            print('Lists configured users.  Configured users can be set as the')
            print('active user (used for all commands going forward) with the')
            print('`set-user` command, or used for a single command with the')
            print('`--as-user` flag.  New users can be added with `linode-cli configure`.')
            print('The user that is currently active is indicated with a `*`')
            exit(0)
        else:
            cli.config.print_users()
            exit(0)

    if parsed.command == "remove-user":
        if parsed.help or not parsed.action:
            print('linode-cli remove-user [USER]')
            print()
            print('Removes a user the CLI was configured with.  This does not change')
            print('your Linode account, only this CLI installation.  Once removed,')
            print('the user may not be set as active or used for commands unless')
            print('configured again.')
            exit(0)
        else:
            cli.config.remove_user(parsed.action)
            exit(0)

    # special command to bake shell completion script
    if parsed.command == 'bake-bash':
        cli.bake_completions()

    # check for plugin invocation
    if parsed.command not in cli.ops and parsed.command in plugins.available:
        context = plugins.PluginContext(cli.token, cli)

        # reconstruct arguments to send to the plugin
        plugin_args = argv[1:] # don't include the program name
        plugin_args.remove(parsed.command) # don't include the plugin name tho

        plugins.invoke(parsed.command, plugin_args, context)
        exit(0)

    if parsed.command not in cli.ops and parsed.command not in plugins.available:
        # unknown commands
        print('Unrecognized command {}'.format(parsed.command))

    # handle a help for a command - either --help or no action triggers this
    if parsed.command is not None and parsed.action is None:
        if parsed.command in cli.ops:
            actions = cli.ops[parsed.command]
            print("linode-cli {} [ACTION]".format(parsed.command))
            print()
            print("Available actions: ")
            content = [[action, op.summary] for action, op in actions.items()]

            header = ['action', 'summary']
            table = SingleTable([header]+content)
            print(table.table)
            exit(0)


    # handle a help for an action
    if parsed.command is not None and parsed.action is not None and parsed.help:
        if parsed.command in cli.ops and parsed.action in cli.ops[parsed.command]:
            operation = cli.ops[parsed.command][parsed.action]
            print("linode-cli {} {}".format(parsed.command, parsed.action), end='')
            for param in operation.params:
                # clean up parameter names - we add an '_' at the end of them
                # during baking if it conflicts with the name of an argument.
                # Remove the trailing underscores on output (they're not
                # important to the end user).
                pname = param.name.upper()
                if pname[-1] == '_':
                    pname = pname[:-1]
                print(' [{}]'.format(pname), end='')
            print()
            print(operation.summary)
            print()
            if operation.args:
                print("Arguments:")
                for arg in sorted(operation.args, key=lambda s: not s.required):
                    print("  --{}: {}{}".format(
                        arg.path,
                        "(required) " if operation.method == 'post' and arg.required else '',
                        arg.description))
            elif operation.method == 'get' and parsed.action == 'list':
                filterable_attrs = ([attr for attr in operation.response_model.attrs
                                     if attr.filterable])

                if filterable_attrs:
                    print("You may filter results with:")
                    for attr in filterable_attrs:
                        print("  --{}".format(attr.name))
        exit(0)

    if parsed.command is not None and parsed.action is not None:
        cli.handle_command(parsed.command, parsed.action, args)
