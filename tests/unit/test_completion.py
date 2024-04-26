#!/usr/local/bin/python3
"""
Unit tests for linodecli.completion
"""

from linodecli import completion


class TestCompletion:
    """
    Unit tests for linodecli.completion
    """

    ops = {"temp_key": {"temp_action": "description"}}
    fish_expected = """# This is a generated file by Linode-CLI! Do not modify!
complete -c linode-cli -n "not __fish_seen_subcommand_from temp_key" -x -a 'temp_key --help'
complete -c linode -n "not __fish_seen_subcommand_from temp_key" -x -a 'temp_key --help'
complete -c lin -n "not __fish_seen_subcommand_from temp_key" -x -a 'temp_key --help'
complete -c linode-cli -n "__fish_seen_subcommand_from temp_key" -x -a 'temp_action --help'
complete -c linode -n "__fish_seen_subcommand_from temp_key" -x -a 'temp_action --help'
complete -c lin -n "__fish_seen_subcommand_from temp_key" -x -a 'temp_action --help'"""
    bash_expected = """# This is a generated file by Linode-CLI! Do not modify!
_linode_cli()
{
local cur prev opts
COMPREPLY=()
cur="${COMP_WORDS[COMP_CWORD]}"
prev="${COMP_WORDS[COMP_CWORD-1]}"

case "${prev}" in
    linode-cli | linode | lin)
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

complete -F _linode_cli linode-cli
complete -F _linode_cli linode
complete -F _linode_cli lin"""

    def test_fish_completion(self, mocker):
        """
        Test if the fish completion renders correctly
        """
        actual = completion.get_fish_completions(self.ops)
        assert actual == self.fish_expected

    def test_bash_completion(self, mocker):
        """
        Test if the bash completion renders correctly
        """
        # mocker = mocker.patch('linodecli-completion.get_bash_completions', return_value=self.bash_expected)
        actual = completion.get_bash_completions(self.ops)
        assert actual == self.bash_expected

    def test_get_completions(self):
        """
        Test get_completions for arg parse
        """
        actual = completion.get_completions(self.ops, False, "bash")
        assert actual == self.bash_expected

        actual = completion.get_completions(self.ops, False, "fish")
        assert actual == self.fish_expected

        actual = completion.get_completions(self.ops, False, "notrealshell")
        assert "invoke" in actual

        actual = completion.get_completions(self.ops, True, "")
        assert "[SHELL]" in actual
