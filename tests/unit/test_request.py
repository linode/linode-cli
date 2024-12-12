class TestRequest:
    """
    Unit tests for baked requests.
    """

    def test_handle_one_ofs(self, post_operation_with_one_ofs):
        args = post_operation_with_one_ofs.args

        arg_map = {arg.path: arg for arg in args}

        print(arg_map.keys())
        expected = {
            "foobar": ("string", "Some foobar.", True),
            "barfoo": ("integer", "Some barfoo.", False),
            "foofoo": ("boolean", "Some foofoo.", False),
            "barbar": ("string", "Some barbar.", False),
        }

        for k, v in expected.items():
            print(k)
            assert arg_map[k].datatype == v[0]
            assert arg_map[k].description == v[1]
            assert arg_map[k].required == v[2]
