import pytest
from openapi3 import OpenAPI
from yaml import safe_load

from linodecli.baked.request import _parse_request_model
from tests.unit.conftest import open_fixture


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

        assert len(arg_map) == len(expected)

        for k, v in expected.items():
            assert arg_map[k].datatype == v[0]
            assert arg_map[k].description == v[1]
            assert arg_map[k].required == v[2]

    @pytest.mark.parametrize("format_marker", ["x-linode-cli-format", "format"])
    @pytest.mark.parametrize("schema_type", [None, "object"])
    def test_json_format_composed_objects(self, format_marker, schema_type):
        with open_fixture("operation_with_one_ofs.yaml") as fixture:
            document = safe_load(fixture)

        variant = document["components"]["schemas"]["Foo"]["oneOf"][1]
        nested_schema = variant["properties"]["barbar"]
        nested_schema[format_marker] = "json"
        if schema_type is not None:
            nested_schema["type"] = schema_type

        schema = OpenAPI(document).components.schemas["Foo"]
        arg_map = {arg.path: arg for arg in _parse_request_model(schema)}

        assert set(arg_map) == {"foobar", "barfoo", "foofoo", "barbar"}
        assert arg_map["barbar"].format == "json"
        assert arg_map["barbar"].datatype == "object"

    @pytest.mark.parametrize("schema_type", ["string", "integer", "array"])
    def test_explicit_non_object_composed_schema(self, schema_type):
        with open_fixture("operation_with_one_ofs.yaml") as fixture:
            document = safe_load(fixture)

        variant = document["components"]["schemas"]["Foo"]["oneOf"][1]
        nested_schema = variant["properties"]["barbar"]
        nested_schema["type"] = schema_type
        for branch in nested_schema["anyOf"]:
            branch.pop("type")
        if schema_type == "array":
            nested_schema["items"] = {"type": "string"}

        schema = OpenAPI(document).components.schemas["Foo"]
        arg_map = {arg.path: arg for arg in _parse_request_model(schema)}

        assert set(arg_map) == {"foobar", "barfoo", "foofoo", "barbar"}
        assert arg_map["barbar"].datatype == schema_type
        assert arg_map["barbar"].format is None
        if schema_type == "array":
            assert arg_map["barbar"].item_type == "string"

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
