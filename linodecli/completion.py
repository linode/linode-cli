#!/usr/local/bin/python3
"""
Contains any code relevant to generating/updating shell completions for linode-cli
"""
from string import Template

from openapi3 import OpenAPI


def get_completions(ops, help_flag, action):
    """
    Handle shell completions based on `linode-cli completion ____`
    """
    if help_flag or not action:
        return (
            "linode-cli completion [SHELL]\n\n"
            "Prints shell completions for the requested shell to stdout.\n"
            "Currently, only completions for bash and fish are available."
        )
    if action == "bash":
        return get_bash_completions(ops)
    if action == "fish":
        return get_fish_completions(ops)
    return (
        "Completions are only available for bash and fish at this time.\n\n"
        "To retrieve these, please invoke as\n"
        "`linode-cli completion bash` or `linode-cli completion fish`"
    )


def get_fish_completions(ops):
    """
    Generates and returns fish shell completions based on the baked spec
    """
    completion_template = Template(
        """# This is a generated file by Linode-CLI! Do not modify!
complete -c linode-cli -n "not __fish_seen_subcommand_from $subcommands" -x -a '$subcommands --help'
complete -c linode -n "not __fish_seen_subcommand_from $subcommands" -x -a '$subcommands --help'
complete -c lin -n "not __fish_seen_subcommand_from $subcommands" -x -a '$subcommands --help'
$command_items"""
    )

    command_template = Template(
        """complete -c linode-cli -n "__fish_seen_subcommand_from $command" \
-x -a '$actions --help'
complete -c linode -n "__fish_seen_subcommand_from $command" \
-x -a '$actions --help'
complete -c lin -n "__fish_seen_subcommand_from $command" \
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
    linode-cli | linode | lin)
        COMPREPLY=( $(compgen -W "$actions --help" -- ${cur}) )
        return 0
        ;;
    $command_items
    *)
        ;;
esac
}

complete -F _linode_cli linode-cli
complete -F _linode_cli linode
complete -F _linode_cli lin"""
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
        if not isinstance(actions, OpenAPI)
    ]

    rendered = completion_template.safe_substitute(
        actions=" ".join(ops.keys()),
        command_items="\n        ".join(command_blocks),
    )

    return rendered
