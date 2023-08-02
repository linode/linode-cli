from linodecli.baked.response import colorize_string


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

    def test_colorize_string(self):
        result = colorize_string("cool", "yellow")

        assert result == "\x1b[33mcool\x1b[0m"

    def test_attr_get_value(self, list_operation_for_response_test):
        model = {"foo": {"bar": "cool"}}
        attr = list_operation_for_response_test.response_model.attrs[0]

        result = attr._get_value(model)

        assert result == "cool"

    def test_attr_get_string(self, list_operation_for_response_test):
        model = {"foo": {"bar": ["cool1", "cool2"]}}
        attr = list_operation_for_response_test.response_model.attrs[0]

        result = attr.get_string(model)

        assert result == "cool1 cool2"

    def test_attr_render_value(self, list_operation_for_response_test):
        model = {"foo": {"bar": ["cool1", "cool2"]}}
        attr = list_operation_for_response_test.response_model.attrs[0]
        attr.color_map = {"default_": "yellow"}

        result = attr.render_value(model)

        assert result == "\x1b[33mcool1, cool2\x1b[0m"
