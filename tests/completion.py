#!/usr/local/bin/python3
"""
Unit tests for linodecli.completion
"""

import unittest
from unittest.mock import patch, mock_open

from linodecli import completion

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
        actual = completion.get_fish_completions(self.ops)
        self.assertEqual(actual, self.fish_expected)

    def test_bash_completion(self):
        """
        Test if the bash completion renders correctly
        """
        actual = completion.get_bash_completions(self.ops)
        self.assertEqual(actual, self.bash_expected)

    def test_get_completions(self):
        """
        Test get_completions for arg parse
        """
        actual = completion.get_completions(self.ops, False, "bash")
        self.assertEqual(actual, self.bash_expected)

        actual = completion.get_completions(self.ops, False, "fish")
        self.assertEqual(actual, self.fish_expected)

        actual = completion.get_completions(self.ops, False, "notrealshell")
        self.assertIn("invoke", actual)

        actual = completion.get_completions(self.ops, True, "")
        self.assertIn("[SHELL]", actual)

    def test_bake_completions(self):
        """
        Test bake_completions write to file
        """
        m = mock_open()
        with patch("linodecli.completion.open", m, create=True):
            new_ops = self.ops
            new_ops["_base_url"] = "bloo"
            new_ops["_spec_version"] = "berry"

            completion.bake_completions(new_ops)

            self.assertNotIn("_base_url", new_ops)
            self.assertNotIn("_spec_version", new_ops)

        m.assert_called_with("linode-cli.sh", "w", encoding="utf-8")
        m.return_value.write.assert_called_once_with(self.bash_expected)
