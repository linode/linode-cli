import pytest

from linodecli.documentation.template_data import (
    Action,
    Argument,
    Param,
    ResponseAttribute,
    Root,
)
from tests.unit.conftest import get_first


class TestDocumentationTemplate:
    @pytest.fixture
    def mock_cli(self, build_mock_cli_with_spec):
        return build_mock_cli_with_spec("docs_template_test.yaml")

    @pytest.fixture
    def mock_cli_with_parsed_template(self, mock_cli):
        template_data = Root.from_cli(mock_cli)
        return mock_cli, template_data

    def test_data_group(self, mock_cli_with_parsed_template):
        _, tmpl_data = mock_cli_with_parsed_template

        assert len(tmpl_data.groups) == 1

        group = get_first(tmpl_data.groups, lambda v: v.name == "test-resource")
        assert group.pretty_name == "Test Resource"
        assert len(group.actions) == 4

    def test_data_action_view(self, mock_cli_with_parsed_template):
        cli, tmpl_data = mock_cli_with_parsed_template

        group = get_first(tmpl_data.groups, lambda v: v.name == "test-resource")
        action = get_first(group.actions, lambda v: v.action[0] == "view")

        assert action.command == "test-resource"
        assert action.action == ["view"]

        assert "linode-cli test-resource view [-h]" in action.usage
        assert "resourceId" in action.usage

        assert "Get information about a test resource." == action.summary
        assert "Get information about a test resource." == action.description
        assert "https://linode.com" == action.api_documentation_url
        assert not action.deprecated

        assert len(action.argument_sections) == 0
        assert len(action.filterable_attributes) == 0

        self._validate_resource_parameters(action)
        self._validate_resource_response_attributes(action)

    def test_data_action_list(self, mock_cli_with_parsed_template):
        cli, tmpl_data = mock_cli_with_parsed_template

        group = get_first(tmpl_data.groups, lambda v: v.name == "test-resource")
        action = get_first(group.actions, lambda v: v.action[0] == "list")

        assert action.command == "test-resource"
        assert action.action == ["list", "ls"]

        assert "linode-cli test-resource list [-h]" in action.usage

        assert "List test resources." == action.summary
        assert "List test resources." == action.description
        assert "https://linode.com" == action.api_documentation_url
        assert not action.deprecated

        assert len(action.argument_sections) == 0
        assert len(action.parameters) == 0

        assert action.filterable_attributes == [
            ResponseAttribute(
                name="boolean_field",
                type="bool",
                description="An arbitrary boolean.",
                example="true",
            )
        ]

        self._validate_resource_response_attributes(action)

    def test_data_action_create(self, mock_cli_with_parsed_template):
        cli, tmpl_data = mock_cli_with_parsed_template

        group = get_first(tmpl_data.groups, lambda v: v.name == "test-resource")
        action = get_first(group.actions, lambda v: v.action[0] == "create")

        assert action.command == "test-resource"
        assert action.action == ["create"]

        assert "linode-cli test-resource create [-h]" in action.usage
        assert "Create a new test resource." == action.summary
        assert "Create a new test resource." == action.description
        assert "https://linode.com" == action.api_documentation_url
        assert not action.deprecated

        assert len(action.parameters) == 0
        assert len(action.samples) == 0
        assert len(action.filterable_attributes) == 0

        self._validate_resource_response_attributes(action)

        arg_sections = action.argument_sections
        assert len(arg_sections) == 2

        assert arg_sections[0].name == ""
        assert arg_sections[0].entries == [
            Argument(
                path="boolean_field",
                required=True,
                type="bool",
                description="An arbitrary boolean.",
                example="true",
            ),
            Argument(
                path="string_field",
                required=True,
                type="str",
                description="An arbitrary string.",
                example="test string",
            ),
            Argument(
                path="object_field.bar",
                required=True,
                type="str",
                description="An arbitrary bar.",
                example="foo",
            ),
            Argument(
                path="integer_field",
                required=False,
                type="int",
                description="An arbitrary integer.",
            ),
            Argument(
                path="literal_list",
                required=False,
                type="[]str",
                description="An arbitrary list of literals.",
                example="foo",
            ),
            Argument(
                path="object_list",
                required=False,
                type="json",
                is_json=True,
                description="An arbitrary object.",
                is_parent=True,
            ),
            Argument(
                path="object_field.foo",
                required=False,
                type="str",
                description="An arbitrary foo.",
                example="bar",
            ),
        ]

        assert arg_sections[1].name == "object_list"
        assert arg_sections[1].entries == [
            Argument(
                path="object_list.field_integer",
                required=True,
                type="int",
                description="An arbitrary nested integer.",
                example="321",
                is_child=True,
                depth=1,
                parent="object_list",
            ),
            Argument(
                path="object_list.field_string",
                required=False,
                type="str",
                description="An arbitrary nested string.",
                example="foobar",
                is_child=True,
                depth=1,
                parent="object_list",
            ),
        ]

    def test_data_action_put(self, mock_cli_with_parsed_template):
        cli, tmpl_data = mock_cli_with_parsed_template

        group = get_first(tmpl_data.groups, lambda v: v.name == "test-resource")
        action = get_first(group.actions, lambda v: v.action[0] == "update")

        assert action.command == "test-resource"
        assert action.action == ["update"]

        assert "linode-cli test-resource update [-h]" in action.usage
        assert "resourceId" in action.usage

        assert "Update a test resource." == action.summary
        assert "Update a test resource." == action.description
        assert "https://linode.com" == action.api_documentation_url
        assert not action.deprecated

        assert len(action.samples) == 0
        assert len(action.filterable_attributes) == 0

        self._validate_resource_parameters(action)
        self._validate_resource_response_attributes(action)

        arg_sections = action.argument_sections
        assert len(arg_sections) == 2

        assert arg_sections[0].name == ""
        assert arg_sections[0].entries == [
            Argument(
                path="object_field.bar",
                required=True,
                type="str",
                description="An arbitrary bar.",
                example="foo",
            ),
            Argument(
                path="boolean_field",
                required=False,
                type="bool",
                description="An arbitrary boolean.",
                example="true",
            ),
            Argument(
                path="integer_field",
                required=False,
                type="int",
                description="An arbitrary integer.",
            ),
            Argument(
                path="literal_list",
                required=False,
                type="[]str",
                description="An arbitrary list of literals.",
                example="foo",
            ),
            Argument(
                path="object_list",
                required=False,
                type="json",
                is_json=True,
                description="An arbitrary object.",
                is_parent=True,
            ),
            Argument(
                path="string_field",
                required=False,
                type="str",
                description="An arbitrary string.",
                example="test string",
            ),
            Argument(
                path="object_field.foo",
                required=False,
                type="str",
                description="An arbitrary foo.",
                example="bar",
            ),
        ]

        assert arg_sections[1].name == "object_list"
        assert arg_sections[1].entries == [
            Argument(
                path="object_list.field_integer",
                required=True,
                type="int",
                description="An arbitrary nested integer.",
                example="321",
                is_child=True,
                depth=1,
                parent="object_list",
            ),
            Argument(
                path="object_list.field_string",
                required=False,
                type="str",
                description="An arbitrary nested string.",
                example="foobar",
                is_child=True,
                depth=1,
                parent="object_list",
            ),
        ]

    @staticmethod
    def _validate_resource_parameters(action: Action):
        assert action.parameters == [
            Param(
                name="resourceId",
                type="int",
                description="The ID of the resource.",
            )
        ]

    @staticmethod
    def _validate_resource_response_attributes(
        action: Action,
    ):
        assert action.attribute_sections_names == {
            "",
            "object_field",
            "object_list",
        }
        assert len(action.attribute_sections) == 3

        sections = action.attribute_sections

        assert sections[0].name == ""
        assert sections[0].entries == [
            ResponseAttribute(
                name="boolean_field",
                type="bool",
                description="An arbitrary boolean.",
                example="true",
            ),
            ResponseAttribute(
                name="literal_list",
                type="[]str",
                description="An arbitrary list of literals.",
                example='["foo", "bar"]',
            ),
            ResponseAttribute(
                name="resource_id",
                type="int",
                description="The ID of this test resource.",
                example="123",
            ),
            ResponseAttribute(
                name="string_field",
                type="str",
                description="An arbitrary string.",
                example="test string",
            ),
        ]

        assert sections[1].name == "object_field"
        assert sections[1].entries == [
            ResponseAttribute(
                name="object_field.bar",
                type="str",
                description="An arbitrary bar.",
                example="foo",
            ),
            ResponseAttribute(
                name="object_field.foo",
                type="str",
                description="An arbitrary foo.",
                example="bar",
            ),
        ]

        assert sections[2].name == "object_list"
        assert sections[2].entries == [
            ResponseAttribute(
                name="object_list.field_integer",
                type="int",
                description="An arbitrary nested integer.",
                example="321",
            ),
            ResponseAttribute(
                name="object_list.field_string",
                type="str",
                description="An arbitrary nested string.",
                example="foobar",
            ),
        ]
