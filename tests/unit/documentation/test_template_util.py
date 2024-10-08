from linodecli.documentation.template_data.util import (
    _format_type,
    _format_usage_text,
    _markdown_to_rst,
    _normalize_padding,
)


class TestDocumentationTemplateUtil:
    def test_normalize_padding(self):
        assert (
            _normalize_padding("foo\n  bar foo\n  test\n    baz\n   wow\n\twow")
            == "foo\n    bar foo\n    test\n        baz\n     wow\n    wow"
        )

    def test_format_usage_text(self):
        assert (
            _format_usage_text(
                "usage: linode-cli foobar [-h] [--foobarfoobar foobarfoobar] [--bar bar] foobarId",
                max_length=28,
            )
            == "linode-cli foobar [-h]\n    [--foobarfoobar foobarfoobar]\n    [--bar bar] foobarId"
        )

    def test_markdown_to_rst(self):
        assert (
            _markdown_to_rst("foo [bar](https://linode.com) bar")
            == "foo `bar <https://linode.com>`_ bar"
        )

    def test_format_type(self):
        assert _format_type("string") == "str"
        assert _format_type("integer") == "int"
        assert _format_type("boolean") == "bool"
        assert _format_type("number") == "float"
        assert _format_type("array", item_type="string") == "[]str"
        assert _format_type("object", _format="json") == "json"
