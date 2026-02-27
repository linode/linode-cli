class TestRequest:
    """
    Unit tests for baked requests.
    """

    def test_handle_one_ofs(self, post_operation_with_one_ofs):
        args = post_operation_with_one_ofs.args

        arg_map = {arg.path: arg for arg in args}

        expected = {
            "foobar": ("string", "Some foobar.", True),
            "barfoo": ("integer", "Some barfoo.", False),
            "foofoo": ("boolean", "Some foofoo.", False),
            "barbar.foo": ("string", "Some foo.", False),
            "barbar.bar": ("integer", "Some bar.", False),
            "barbar.baz": ("boolean", "Some baz.", False),
        }

        for k, v in expected.items():
            assert arg_map[k].datatype == v[0]
            assert arg_map[k].description == v[1]
            assert arg_map[k].required == v[2]

    def test_skip_request_attributes(self, post_skip_test_operation):
        """
        Test that request attributes with x-linode-cli-skip extension are excluded.
        """
        args = post_skip_test_operation.args
        arg_map = {arg.path: arg for arg in args}

        # These fields should be present
        assert "visible_field" in arg_map
        assert "another_visible_field" in arg_map
        assert "nested_object.nested_visible_field" in arg_map

        # These fields should be skipped
        assert "skipped_request_field" not in arg_map
        assert "skipped_both_field" not in arg_map
        assert "nested_object.nested_skipped_field" not in arg_map
