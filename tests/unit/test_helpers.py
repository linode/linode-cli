from linodecli.helpers import filter_markdown_links


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
