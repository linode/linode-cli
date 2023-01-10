#!/usr/local/bin/python3
"""
Unit tests for linodecli.completion
"""

import unittest
from linodecli.completion import get_bash_completions

class CompletionTests(unittest.TestCase):
    """
    Unit tests for linodecli.completion
    """

    def test_bash_completion(self):
        """
        Test if the bash completion renders correctly
        """
        ops = {
                "temp_key": {"temp_action": "description"},
                "temp_key2": {"temp_action2": "description"},
        }
        expected = """# This is a generated file by Linode-CLI! Do not modify!
_linode_cli()
{
local cur prev opts
COMPREPLY=()
cur="${COMP_WORDS[COMP_CWORD]}"
prev="${COMP_WORDS[COMP_CWORD-1]}"

case "${prev}" in
    linode-cli)
        COMPREPLY=( $(compgen -W "temp_key temp_key2 --help" -- ${cur}) )
        return 0
        ;;
    temp_key)
        COMPREPLY=( $(compgen -W "temp_action --help" -- ${cur}) )
        return 0
        ;;
        temp_key2)
        COMPREPLY=( $(compgen -W "temp_action2 --help" -- ${cur}) )
        return 0
        ;;
    *)
        ;;
esac
}

complete -F _linode_cli linode-cli"""
        actual = get_bash_completions(ops)
        self.assertEqual(actual, expected)
