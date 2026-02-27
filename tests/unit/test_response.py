class TestResponse:
    """
    Unit tests for baked responses.
    """

    def test_model_fix_json_rows(self, list_operation_for_response_test):
        model = list_operation_for_response_test.response_model
        model.rows = ["foo.bar", "bar"]
        result = model.fix_json({"foo": {"bar": 123}, "bar": "cool"})

        assert result == [123, "cool"]

    def test_model_fix_json_nested(self, list_operation_for_response_test):
        model = list_operation_for_response_test.response_model
        model.nested_list = "foo.cool"

        result = model.fix_json([{"foo": {"cool": [123, 321]}}])

        assert result == [
            {"_split": "cool", "foo": 123},
            {"_split": "cool", "foo": 321},
        ]

    def test_attr_get_value(self, list_operation_for_response_test):
        model = {"data": {"foo": {"bar": "cool"}}}
        attr = list_operation_for_response_test.response_model.attrs[0]

        result = attr._get_value(model)

        assert result == "cool"

    def test_attr_get_string(self, list_operation_for_response_test):
        model = {"data": {"foo": {"bar": ["cool1", "cool2"]}}}
        attr = list_operation_for_response_test.response_model.attrs[0]

        result = attr.get_string(model)

        assert result == "cool1 cool2"

    def test_attr_render_value(self, list_operation_for_response_test):
        model = {"data": {"foo": {"bar": ["cool1", "cool2"]}}}
        attr = list_operation_for_response_test.response_model.attrs[0]
        attr.color_map = {"default_": "yellow"}

        result = attr.render_value(model)

        assert result == "[yellow]cool1, cool2[/]"

    def test_handle_one_ofs(self, post_operation_with_one_ofs):
        model = post_operation_with_one_ofs.response_model

        attr_map = {attr.path: attr for attr in model.attrs}

        expected = {
            "foobar": ("string", "Some foobar"),
            "barfoo": ("integer", "Some barfoo"),
            "foofoo": ("boolean", "Some foofoo"),
            "barbar.foo": ("string", "Some foo"),
            "barbar.bar": ("integer", "Some bar"),
            "barbar.baz": ("boolean", "Some baz"),
        }

        for k, v in expected.items():
            assert attr_map[k].datatype == v[0]
            assert attr_map[k].description == v[1]

    def test_fix_json_string_type(self, list_operation_for_response_test):
        model = list_operation_for_response_test.response_model
        model.rows = ["foo.bar", "type"]

        input_json = {"foo": {"bar": "string_value"}, "type": "example_type"}
        result = model.fix_json(input_json)

        assert result == ["string_value", "example_type"]

    def test_fix_json_integer_type(self, list_operation_for_response_test):
        model = list_operation_for_response_test.response_model
        model.rows = ["size", "id"]

        input_json = {"size": 42, "id": 123}
        result = model.fix_json(input_json)

        assert result == [42, 123]

    def test_dictionary_like_property(self, list_operation_for_response_test):
        model = list_operation_for_response_test.response_model

        model.rows = ["dictLike"]

        input_data = {"dictLike": {"keyA": "valueA", "keyB": "valueB"}}

        result = model.fix_json(input_data)
        assert result == [{"keyA": "valueA", "keyB": "valueB"}]

    def test_standard_object_property(self, list_operation_for_response_test):
        model = list_operation_for_response_test.response_model

        # Set rows to include the standard object
        model.rows = ["standard"]

        # Simulate input data
        input_data = {"standard": {"key1": "test", "key2": 42}}

        result = model.fix_json(input_data)
        assert result == [{"key1": "test", "key2": 42}]

    def test_array_of_objects_property(self, list_operation_for_response_test):
        model = list_operation_for_response_test.response_model

        model.rows = ["objectArray"]

        # Simulate input data
        input_data = {
            "objectArray": [
                {"subkey1": "item1", "subkey2": True},
                {"subkey1": "item2", "subkey2": False},
            ]
        }

        result = model.fix_json(input_data)
        assert result == [
            {"subkey1": "item1", "subkey2": True},
            {"subkey1": "item2", "subkey2": False},
        ]

    def test_skip_response_attributes(self, get_skip_test_operation):
        """
        Test that response attributes with x-linode-cli-skip extension are excluded.
        """
        model = get_skip_test_operation.response_model
        attr_map = {attr.name: attr for attr in model.attrs}

        # These fields should be present
        assert "id" in attr_map
        assert "visible_field" in attr_map
        assert "another_visible_field" in attr_map
        assert "nested_object.nested_visible_field" in attr_map

        # These fields should be skipped
        assert "skipped_response_field" not in attr_map
        assert "skipped_both_field" not in attr_map
        assert "nested_object.nested_skipped_field" not in attr_map

    def test_skip_attributes_in_both_request_and_response(
        self, post_skip_test_operation, get_skip_test_operation
    ):
        """
        Test that attributes marked with x-linode-cli-skip are excluded from both
        request and response models.
        """
        # Test request model
        request_args = post_skip_test_operation.args
        request_arg_map = {arg.path: arg for arg in request_args}

        # Test response model
        response_model = get_skip_test_operation.response_model
        response_attr_map = {attr.name: attr for attr in response_model.attrs}

        # The skipped_both_field should not appear in either model
        assert "skipped_both_field" not in request_arg_map
        assert "skipped_both_field" not in response_attr_map

        # But visible fields should appear in both
        assert "visible_field" in request_arg_map
        assert "visible_field" in response_attr_map
        assert "another_visible_field" in request_arg_map
        assert "another_visible_field" in response_attr_map
