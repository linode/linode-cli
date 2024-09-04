
import pytest

from linodecli.documentation.template_data import (
    Action,
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
        assert action.deprecated is None

        assert len(action.parameters) == 0
        assert len(action.samples) == 0
        assert len(action.filterable_attributes) == 0
        # assert len(action.argument_sections) == 0
        # assert len(action.argument_sections_names) == 0

        assert len(action.attribute_sections)
        self._validate_resource_response_attributes(action)

    @staticmethod
    def _validate_resource_response_attributes(
        action: Action,
    ):
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
