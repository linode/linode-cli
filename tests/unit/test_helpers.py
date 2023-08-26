from argparse import ArgumentParser

from linodecli.helpers import (
    filter_markdown_links,
    pagination_args_shared,
    register_args_shared,
)


class TestHelpers:
    """
    Unit tests for linodecli.helpers
    """

    def test_markdown_links(self):
        original_text = "Here's [a relative link](/docs/cool) and [an absolute link](https://cloud.linode.com)."
        expected_text = (
            "Here's a relative link (https://linode.com/docs/cool) "
            "and an absolute link (https://cloud.linode.com)."
        )

        assert filter_markdown_links(original_text) == expected_text

    def test_pagination_args_shared(self):
        parser = ArgumentParser()
        pagination_args_shared(parser)

        args = parser.parse_args(
            ["--page", "2", "--page-size", "50", "--all-rows"]
        )
        assert args.page == 2
        assert args.page_size == 50
        assert args.all_rows

    def test_register_args_shared(self):
        parser = ArgumentParser()
        register_args_shared(parser)

        args = parser.parse_args(
            ["--as-user", "linode-user", "--suppress-warnings"]
        )
        assert args.as_user == "linode-user"
        assert args.suppress_warnings
