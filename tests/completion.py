#!/usr/local/bin/python3
"""
Unit tests for linodecli.completion
"""

import unittest
from linodecli.completion import get_completions, get_bash_completions, get_fish_completions

class CompletionTests(unittest.TestCase):
    """
    Unit tests for linodecli.completion
    """

    ops = {"temp_key": {"temp_action": "description"}}
    fish_expected = """# This is a generated file by Linode-CLI! Do not modify!
complete -c linode-cli -n "not __fish_seen_subcommand_from temp_key" -x -a 'temp_key --help'
complete -c linode-cli -n "__fish_seen_subcommand_from temp_key" -x -a 'temp_action --help'"""
    bash_expected = """# This is a generated file by Linode-CLI! Do not modify!
_linode_cli()
{
local cur prev opts
COMPREPLY=()
cur="${COMP_WORDS[COMP_CWORD]}"
prev="${COMP_WORDS[COMP_CWORD-1]}"

case "${prev}" in
    linode-cli)
        COMPREPLY=( $(compgen -W "temp_key --help" -- ${cur}) )
        return 0
        ;;
    temp_key)
        COMPREPLY=( $(compgen -W "temp_action --help" -- ${cur}) )
        return 0
        ;;
    *)
        ;;
esac
}

complete -F _linode_cli linode-cli"""

    def test_fish_completion(self):
        """
        Test if the fish completion renders correctly
        """
        actual = get_fish_completions(self.ops)
        self.assertEqual(actual, self.fish_expected)

    def test_bash_completion(self):
        """
        Test if the bash completion renders correctly
        """
        actual = get_bash_completions(self.ops)
        self.assertEqual(actual, self.bash_expected)

    def test_get_completions(self):
        """
        Test get_completions for arg parse
        """
        actual = get_completions(self.ops, False, "bash")
        self.assertEqual(actual, self.bash_expected)

        actual = get_completions(self.ops, False, "fish")
        self.assertEqual(actual, self.fish_expected)

        actual = get_completions(self.ops, False, "notrealshell")
        self.assertIn("invoke", actual)

        actual = get_completions(self.ops, True, "")
        self.assertIn("[SHELL]", actual)
