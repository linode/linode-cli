"""
Contains the template data for Linode CLI actions.
"""

from dataclasses import dataclass, field
from io import StringIO
from typing import List, Optional, Self, Set

from linodecli.baked import OpenAPIOperation
from linodecli.baked.request import OpenAPIRequestArg
from linodecli.documentation.template_data.argument import Argument
from linodecli.documentation.template_data.attribute import ResponseAttribute
from linodecli.documentation.template_data.field_section import FieldSection
from linodecli.documentation.template_data.param import Param
from linodecli.documentation.template_data.util import (
    _format_usage_text,
    _markdown_to_rst,
    _normalize_padding,
)


@dataclass
class Action:
    """
    Represents a single generated Linode CLI command/action.
    """

    command: str
    action: List[str]

    usage: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    api_documentation_url: Optional[str] = None
    deprecated: bool = False
    parameters: List[Param] = field(default_factory=lambda: [])
    samples: List[str] = field(default_factory=lambda: [])
    attributes: List[ResponseAttribute] = field(default_factory=lambda: [])
    filterable_attributes: List[ResponseAttribute] = field(
        default_factory=lambda: []
    )

    argument_sections: List[FieldSection[Argument]] = field(
        default_factory=lambda: []
    )
    argument_sections_names: Set[str] = field(default_factory=lambda: {})

    attribute_sections: List[FieldSection[ResponseAttribute]] = field(
        default_factory=lambda: []
    )
    attribute_sections_names: Set[str] = field(default_factory=lambda: {})

    @classmethod
    def from_openapi(cls, operation: OpenAPIOperation) -> Self:
        """
        Returns a new Action object initialized using values
        from the given operation.

        :param operation: The operation to initialize the object with.

        :returns: The initialized object.
        """

        result = cls(
            command=operation.command,
            action=[operation.action] + (operation.action_aliases or []),
            summary=_markdown_to_rst(operation.summary),
            description=(
                _markdown_to_rst(operation.description)
                if operation.description != ""
                else None
            ),
            usage=cls._get_usage(operation),
            api_documentation_url=operation.docs_url,
            deprecated=operation.deprecated is not None
            and operation.deprecated,
        )

        if operation.samples:
            result.samples = [
                _normalize_padding(sample["source"])
                for sample in operation.samples
            ]

        if operation.params:
            result.parameters = [
                Param.from_openapi(param) for param in operation.params
            ]

        if operation.method == "get" and operation.response_model.is_paginated:
            result.filterable_attributes = sorted(
                [
                    ResponseAttribute.from_openapi(attr)
                    for attr in operation.response_model.attrs
                    if attr.filterable
                ],
                key=lambda v: v.name,
            )

        if operation.args:
            result.argument_sections = FieldSection.from_iter(
                iter(
                    Argument.from_openapi(arg)
                    for arg in operation.args
                    if isinstance(arg, OpenAPIRequestArg) and not arg.read_only
                ),
                get_parent=lambda arg: arg.parent if arg.is_child else None,
                sort_key=lambda arg: (
                    not arg.required,
                    "." in arg.path,
                    arg.path,
                ),
            )

            result.argument_sections_names = {
                section.name for section in result.argument_sections
            }

        if operation.response_model.attrs:
            result.attribute_sections = FieldSection.from_iter(
                iter(
                    ResponseAttribute.from_openapi(attr)
                    for attr in operation.response_model.attrs
                ),
                get_parent=lambda attr: (
                    attr.name.split(".", maxsplit=1)[0]
                    if "." in attr.name
                    else None
                ),
                sort_key=lambda attr: attr.name,
            )

            result.attribute_sections_names = {
                section.name for section in result.attribute_sections
            }

        return result

    @staticmethod
    def _get_usage(operation: OpenAPIOperation) -> str:
        """
        Returns the formatted argparse usage string for the given operation.

        :param: operation: The operation to get the usage string for.

        :returns: The formatted usage string.
        """

        usage_io = StringIO()
        operation.build_parser()[0].print_usage(file=usage_io)

        return _format_usage_text(usage_io.getvalue())
