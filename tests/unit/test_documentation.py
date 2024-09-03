from linodecli.documentation.filters import _filter_truncate_middle


class TestDocumentation:
    def test_filter_truncation_middle(self):
        assert (
            _filter_truncate_middle("foobarfoobar", length=12) == "foobarfoobar"
        )
        assert _filter_truncate_middle("foobarfoobar", length=6) == "foo...bar"
        assert _filter_truncate_middle("foobarfoobar", length=2) == "f...r"
        assert _filter_truncate_middle("foobarodd", length=5) == "foo...dd"
