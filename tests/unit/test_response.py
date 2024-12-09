class TestOutputHandler:
    """
    Unit tests for linodecli.response
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
