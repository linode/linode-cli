from types import SimpleNamespace

from linodecli import help_pages


class TestHelpPages:
    def test_filter_markdown_links(self):
        """
        Ensures that Markdown links are properly converted to their rich equivalents.
        """

        original_text = "Here's [a relative link](/docs/cool) and [an absolute link](https://cloud.linode.com)."
        expected_text = (
            "Here's a relative link ([link=https://linode.com/docs/cool]https://linode.com/docs/cool[/link]) "
            "and an absolute link ([link=https://cloud.linode.com]https://cloud.linode.com[/link])."
        )

        assert (
            help_pages._markdown_links_to_rich(original_text) == expected_text
        )

    def test_group_arguments(self, capsys):
        # NOTE: We use SimpleNamespace here so we can do deep comparisons using ==
        args = [
            SimpleNamespace(
                read_only=False,
                required=True,
                path="foo",
            ),
            SimpleNamespace(read_only=False, required=False, path="foo.bar"),
            SimpleNamespace(read_only=False, required=False, path="foobaz"),
            SimpleNamespace(read_only=False, required=False, path="foo.foo"),
            SimpleNamespace(read_only=False, required=False, path="foobar"),
            SimpleNamespace(read_only=False, required=True, path="barfoo"),
        ]

        expected = [
            [
                SimpleNamespace(read_only=False, required=True, path="barfoo"),
            ],
            [
                SimpleNamespace(read_only=False, required=False, path="foobar"),
                SimpleNamespace(read_only=False, required=False, path="foobaz"),
            ],
            [
                SimpleNamespace(
                    read_only=False,
                    required=True,
                    path="foo",
                ),
                SimpleNamespace(
                    read_only=False, required=False, path="foo.bar"
                ),
                SimpleNamespace(
                    read_only=False, required=False, path="foo.foo"
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
        help_pages.print_help_default(mock_ops, mocked_config)
        captured = capsys.readouterr()
        assert "testkey1" in captured.out

    def test_help_with_ops_with_plugins(self, capsys, mocker, mocked_config):
        mock_ops = {"testkey1": "testvalue1"}
        mocker.patch(
            "linodecli.arg_helpers.plugins.available",
            return_value=["testing.plugin"],
        )
        help_pages.print_help_default(mock_ops, mocked_config)
        captured = capsys.readouterr()
        assert "testing.plugin" in captured.out

    # arg_helpers.print_help_action(cli, command, action)
    def test_action_help_value_error(self, capsys, mock_cli):
        help_pages.print_help_action(mock_cli, None, None)
        captured = capsys.readouterr()
        assert not captured.out

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
                depth=0,
            ),
            mocker.MagicMock(
                read_only=False,
                required=False,
                path="path2",
                description="test description 2",
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
