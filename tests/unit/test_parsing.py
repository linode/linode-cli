from linodecli.baked.parsing import (
    extract_markdown_links,
    get_short_description,
    markdown_to_rich_markup,
    strip_techdocs_prefixes,
)


class TestParsing:
    """
    Unit tests for linodecli.parsing
    """

    def test_extract_markdown_links(self):
        """
        Ensures that Markdown links are properly extracted and removed from a string.
        """

        original_text = "Here's [a relative link](/docs/cool) and [an absolute link](https://cloud.linode.com)."

        result_text, result_links = extract_markdown_links(original_text)

        assert result_text == "Here's a relative link and an absolute link."
        assert result_links == [
            "https://linode.com/docs/cool",
            "https://cloud.linode.com",
        ]

    def test_get_first_sentence(self):
        assert (
            get_short_description(
                "This is a sentence. This is another sentence."
            )
            == "This is a sentence."
        )

        # New line delimiter
        assert (
            get_short_description(
                "This is a sentence.\nThis is another sentence."
            )
            == "This is a sentence."
        )

        # Multi-space delimiter
        assert (
            get_short_description(
                "This is a sentence.   This is another sentence."
            )
            == "This is a sentence."
        )

        # Tab delimiter
        assert (
            get_short_description(
                "This is a sentence.    This is another sentence."
            )
            == "This is a sentence."
        )

        assert (
            get_short_description("This is a sentence.")
            == "This is a sentence."
        )

        assert (
            get_short_description(
                "__Note__ This might be a sentence.\nThis is a sentence."
            )
            == "This is a sentence."
        )

    def test_get_techdocs_prefixes(self):
        assert (
            strip_techdocs_prefixes(
                "__Read-only__ The last successful backup date. 'null' if there was no previous backup.",
            )
            == "The last successful backup date. 'null' if there was no previous backup."
        )

        assert (
            strip_techdocs_prefixes(
                "__Filterable__, __Read-only__ This Linode's ID which "
                "must be provided for all operations impacting this Linode.",
            )
            == "This Linode's ID which must be provided for all operations impacting this Linode."
        )

        assert (
            strip_techdocs_prefixes(
                "Do something cool.",
            )
            == "Do something cool."
        )

    def test_markdown_to_rich_markup(self):
        assert (
            markdown_to_rich_markup(
                "very *cool* **test** _string_*\n__wow__ *cool** `code block` `"
            )
            == "very [i]cool[/] [b]test[/] [i]string[/]*\n[b]wow[/] [i]cool[/]* "
            "[italic deep_pink3 on grey15]code block[/] `"
        )
