#!/usr/local/bin/python3
"""
Contains any code relevant to generating/updating shell completions for linode-cli
"""

import sys
from string import Template

def bake_completions(cli):
    """
    Given a baked CLI, generates and saves a bash completion file
    """
    print("Baking bash completions...")
    if "_base_url" in cli.ops:
        del cli.ops["_base_url"]
    if "_spec_version" in cli.ops:
        del cli.ops["_spec_version"]
    rendered = get_bash_completions(cli)
    with open("linode-cli.sh", "w", encoding="utf-8") as bash_f:
        print("Writing file...")
        bash_f.write(rendered)

def get_completions(ops, help_flag, action):
    """
    Handle shell completions based on `linode-cli completion ____`
    """
    if help_flag or not action:
        print("linode-cli completion [SHELL]")
        print()
        print(
            "Prints shell completions for the requested shell to stdout. "
            "Currently, only completions for bash and fish are available."
        )
        sys.exit(0)

    completions = ""

    if action == "bash":
        completions = get_bash_completions(ops)
    elif action == "fish":
        completions = get_fish_completions(ops)
    else:
        print(
            "Completions are only available for bash and fish at this time. "
            "To retrieve these, please invoke as "
            "`linode-cli completion bash` or `linode-cli completion fish`."
        )
        sys.exit(1)

    print(completions)
    sys.exit(0)

def get_fish_completions(ops):
    """
    Generates and returns fish shell completions based on the baked spec
    """
    completion_template = Template(
        """# This is a generated file by Linode-CLI! Do not modify!
complete -c linode-cli -n "not __fish_seen_subcommand_from $subcommands" -x -a '$subcommands --help'
$command_items"""
    )

    command_template = Template(
        """complete -c linode-cli -n "__fish_seen_subcommand_from $command" \
                -x -a '$actions --help'"""
    )

    command_blocks = [
        command_template.safe_substitute(
            command=op, actions=" ".join(list(actions.keys()))
        )
        for op, actions in ops.items()
    ]

    rendered = completion_template.safe_substitute(
        subcommands=" ".join(ops.keys()),
        command_items="\n".join(command_blocks),
    )

    return rendered

def get_bash_completions(ops):
    """
    Generates and returns bash shell completions based on the baked spec
    """
    completion_template = Template(
        """# This is a generated file by Linode-CLI! Do not modify!
_linode_cli()
{
local cur prev opts
COMPREPLY=()
cur="${COMP_WORDS[COMP_CWORD]}"
prev="${COMP_WORDS[COMP_CWORD-1]}"

case "${prev}" in
    linode-cli)
        COMPREPLY=( $(compgen -W "$actions --help" -- ${cur}) )
        return 0
        ;;
    $command_items
    *)
        ;;
esac
}

complete -F _linode_cli linode-cli"""
    )

    command_template = Template(
        """$command)
        COMPREPLY=( $(compgen -W "$actions --help" -- ${cur}) )
        return 0
        ;;"""
    )

    command_blocks = [
        command_template.safe_substitute(
            command=op, actions=" ".join(list(actions.keys()))
        )
        for op, actions in ops.items()
    ]

    rendered = completion_template.safe_substitute(
        actions=" ".join(ops.keys()),
        command_items="\n        ".join(command_blocks),
    )

    return rendered
