from typing import List

import pytest

from linodecli.documentation.template_data import Root, FieldSection, ResponseAttribute
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
        assert len(action.argument_sections) == 0
        assert len(action.argument_sections_names) == 0

        assert len(action.attribute_sections)



    @staticmethod
    def _validate_resource_response_attributes(
        sections: List[FieldSection[ResponseAttribute]],
    ):
        assert len(sections) == 1

        section = sections[0]

        assert section.name == ""
        assert len(section.entries) == 1

        entry = sections[0].entries[0]
        assert entry.name == "resource_id"
        assert entry.type == "int"
        assert entry.description == "The ID of this test resource."
        assert entry.example == 123
