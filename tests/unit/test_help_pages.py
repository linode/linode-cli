import contextlib
from io import StringIO
from types import SimpleNamespace

import pytest

from linodecli import CLI, help_pages
from linodecli.baked import OpenAPIOperation
from tests.unit.conftest import assert_contains_ordered_substrings


class TestHelpPages:
    def test_group_arguments(self, capsys):
        # NOTE: We use SimpleNamespace here so we can do deep comparisons using ==
        args = [
            SimpleNamespace(
                read_only=False,
                required=False,
                depth=0,
                path="foobaz",
                parent=None,
                is_parent=False,
            ),
            SimpleNamespace(
                read_only=False,
                required=False,
                depth=0,
                path="foobar",
                parent=None,
                is_parent=False,
            ),
            SimpleNamespace(
                read_only=False,
                required=True,
                depth=0,
                path="barfoo",
                parent=None,
                is_parent=False,
            ),
            SimpleNamespace(
                read_only=False,
                required=False,
                depth=0,
                path="foo",
                parent=None,
                is_parent=True,
            ),
            SimpleNamespace(
                read_only=False,
                required=False,
                depth=1,
                path="foo.bar",
                parent="foo",
                is_parent=False,
            ),
            SimpleNamespace(
                read_only=False,
                required=False,
                depth=1,
                path="foo.foo",
                parent="foo",
                is_parent=False,
            ),
            SimpleNamespace(
                read_only=False,
                required=True,
                depth=1,
                path="foo.baz",
                parent="foo",
                is_parent=True,
            ),
            SimpleNamespace(
                read_only=False,
                required=True,
                depth=1,
                path="foo.foobar",
                parent="foo",
                is_parent=False,
            ),
            SimpleNamespace(
                read_only=False,
                required=True,
                depth=2,
                path="foo.baz.foo",
                parent="foo.baz",
                is_parent=False,
            ),
            SimpleNamespace(
                read_only=False,
                required=True,
                depth=2,
                path="foo.baz.bar",
                parent="foo.baz",
                is_parent=False,
            ),
        ]

        expected = [
            [
                SimpleNamespace(
                    read_only=False,
                    required=True,
                    path="barfoo",
                    depth=0,
                    parent=None,
                    is_parent=False,
                ),
            ],
            [
                SimpleNamespace(
                    read_only=False,
                    required=False,
                    path="foobar",
                    depth=0,
                    parent=None,
                    is_parent=False,
                ),
                SimpleNamespace(
                    read_only=False,
                    required=False,
                    path="foobaz",
                    depth=0,
                    parent=None,
                    is_parent=False,
                ),
            ],
            [
                SimpleNamespace(
                    read_only=False,
                    required=False,
                    path="foo",
                    depth=0,
                    parent=None,
                    is_parent=True,
                ),
                SimpleNamespace(
                    read_only=False,
                    required=True,
                    depth=1,
                    path="foo.foobar",
                    parent="foo",
                    is_parent=False,
                ),
                SimpleNamespace(
                    read_only=False,
                    required=False,
                    path="foo.bar",
                    depth=1,
                    parent="foo",
                    is_parent=False,
                ),
                SimpleNamespace(
                    read_only=False,
                    required=False,
                    path="foo.foo",
                    depth=1,
                    parent="foo",
                    is_parent=False,
                ),
            ],
            [
                SimpleNamespace(
                    read_only=False,
                    required=True,
                    path="foo.baz",
                    depth=1,
                    parent="foo",
                    is_parent=True,
                ),
                SimpleNamespace(
                    read_only=False,
                    required=True,
                    depth=2,
                    path="foo.baz.bar",
                    parent="foo.baz",
                    is_parent=False,
                ),
                SimpleNamespace(
                    read_only=False,
                    required=True,
                    depth=2,
                    path="foo.baz.foo",
                    parent="foo.baz",
                    is_parent=False,
                ),
            ],
        ]

        assert help_pages._help_group_arguments(args) == expected

    def test_action_help_get_method(self, capsys, mocker, mock_cli):
        mocked_ops = mocker.MagicMock()
        mocked_ops.summary = "test summary"
        mocked_ops.docs_url = "https://website.com/endpoint"
        mocked_ops.method = "get"
        mocked_ops.action = "list"
        mocked_ops.args = None
        mocked_ops.samples = [
            {"lang": "CLI", "source": "linode-cli command action"}
        ]

        mock_attr = mocker.MagicMock()
        mock_attr.filterable = True
        mock_attr.name = "filtername"
        mocked_ops.response_model.attrs = [mock_attr]

        mock_cli.find_operation = mocker.Mock(return_value=mocked_ops)

        help_pages.print_help_action(mock_cli, "command", "action")
        captured = capsys.readouterr()
        assert "test summary" in captured.out
        assert "API Documentation" in captured.out
        assert "https://website.com/endpoint" in captured.out
        assert "Example Usage: \n  linode-cli command action" in captured.out
        assert "Arguments" not in captured.out
        assert "filter results" in captured.out
        assert "filtername" in captured.out

    def test_help_with_ops(self, capsys, mocked_config):
        mock_ops = {"testkey1": "testvalue1"}
        help_pages.print_help_commands(mock_ops)
        captured = capsys.readouterr()
        assert "testkey1" in captured.out

    def test_help_with_ops_with_plugins(self, capsys, mocker, mocked_config):
        mocker.patch(
            "linodecli.help_pages.plugins.available",
            return_value=["testing.plugin"],
        )
        help_pages.print_help_plugins(mocked_config)
        captured = capsys.readouterr()
        assert "testing.plugin" in captured.out

    def test_help_with_env_vars(self, capsys):
        help_pages.print_help_env_vars()
        captured = capsys.readouterr()
        for var in help_pages.HELP_ENV_VARS:
            assert var in captured.out

    def test_help_topics(self, capsys):
        help_pages.print_help_default()
        captured = capsys.readouterr()
        for topic in help_pages.HELP_TOPICS:
            assert topic in captured.out

    # arg_helpers.print_help_action(cli, command, action)
    def test_action_help_value_error(
        self, capsys, mock_cli: CLI, create_operation: OpenAPIOperation
    ):
        mock_cli.ops = {
            "foo": {
                "bar": create_operation,
            }
        }

        stderr_buf = StringIO()

        with pytest.raises(SystemExit), contextlib.redirect_stderr(stderr_buf):
            help_pages.print_help_action(mock_cli, "fake", "fake")

        assert "Command not found: fake" in stderr_buf.getvalue()

        stderr_buf = StringIO()

        with pytest.raises(SystemExit), contextlib.redirect_stderr(stderr_buf):
            help_pages.print_help_action(mock_cli, "foo", "fake")

        assert "Action not found for command foo: fake" in stderr_buf.getvalue()

    def test_action_help_post_method(self, capsys, mocker, mock_cli):
        mocked_ops = mocker.MagicMock()
        mocked_ops.summary = "test summary"
        mocked_ops.docs_url = "https://website.com/endpoint"
        mocked_ops.method = "post"
        mocked_ops.samples = [
            {"lang": "CLI", "source": "linode-cli command action\n  --foo=bar"},
            {"lang": "CLI", "source": "linode-cli command action\n  --bar=foo"},
        ]

        mocked_ops.args = [
            mocker.MagicMock(
                read_only=False,
                required=True,
                path="path",
                description="test description",
                description_rich="test description",
                depth=0,
            ),
            mocker.MagicMock(
                read_only=False,
                required=False,
                path="path2",
                description="test description 2",
                description_rich="test description 2",
                format="json",
                nullable=True,
                depth=0,
            ),
        ]

        mock_cli.find_operation = mocker.Mock(return_value=mocked_ops)

        help_pages.print_help_action(mock_cli, "command", "action")
        captured = capsys.readouterr()

        assert "test summary" in captured.out
        assert "API Documentation" in captured.out
        assert "https://website.com/endpoint" in captured.out
        assert (
            "Example Usages: \n"
            "  linode-cli command action\n"
            "    --foo=bar\n\n"
            "  linode-cli command action\n"
            "    --bar=foo\n\n"
        ) in captured.out
        assert "Arguments" in captured.out
        assert "test description" in captured.out
        assert "test description 2" in captured.out
        assert "(required, nullable, conflicts with children)" in captured.out
        assert "(JSON, nullable, conflicts with children)" in captured.out
        assert "filter results" not in captured.out

    def test_help_command_actions(self, mocker):
        test_operations = {
            "foo": {
                "b-create": mocker.MagicMock(
                    summary="Test summary.", action_aliases=[]
                ),
                "b-list": mocker.MagicMock(
                    summary="Test summary 2.", action_aliases=["b-ls"]
                ),
                "a-list": mocker.MagicMock(
                    summary="Test summary 3.", action_aliases=["a-ls"]
                ),
            }
        }

        stdout_buffer = StringIO()
        help_pages.print_help_command_actions(
            test_operations, "foo", file=stdout_buffer
        )

        # Ensure the given snippets are printed in order, ignoring irrelevant characters
        assert_contains_ordered_substrings(
            stdout_buffer.getvalue(),
            [
                "linode-cli foo [ACTION]",
                "Available actions:",
                "action",
                "summary",
                "a-list, a-ls",
                "Test summary 3.",
                "b-create",
                "Test summary.",
                "b-list, b-ls",
                "Test summary 2.",
            ],
        )

    def test_action_help_post_method_routed(
        self, capsys, mocker, mock_cli, post_operation_with_one_ofs
    ):
        mock_cli.find_operation = mocker.Mock(
            return_value=post_operation_with_one_ofs
        )

        help_pages.print_help_action(mock_cli, "command", "action")
        captured = capsys.readouterr().out

        print(captured)

        assert "linode-cli command action" in captured
        assert "Do something." in captured

        assert "Arguments (Usage 1):" in captured
        assert "--foobar (required): Some foobar." in captured
        assert "--foofoo (required): Some foofoo." in captured

        assert "Arguments (Usage 2):" in captured
        assert "--foobar (required): Some foobar." in captured
        assert "--foofoo (required): Some foofoo." in captured

        assert "--barbar.bar: Some bar." in captured
        assert "--barbar.baz: Some baz." in captured
        assert "--barbar.foo: Some foo." in captured
