"""
Contains all structures used to render documentation templates.
"""

import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from io import StringIO
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Self,
    Set,
    TypeVar,
)

from linodecli.baked import OpenAPIOperation
from linodecli.baked.operation import OpenAPIOperationParameter
from linodecli.baked.request import OpenAPIRequestArg
from linodecli.baked.response import OpenAPIResponseAttr
from linodecli.cli import CLI
from linodecli.documentation.util import (
    _format_type,
    _format_usage_text,
    _markdown_to_rst,
    _normalize_padding,
)
from linodecli.helpers import sorted_actions_smart

# Manual corrections to the generated "pretty" names for command groups.
GROUP_NAME_CORRECTIONS = {
    "lke": "LKE",
    "nodebalancers": "NodeBalancer",
    "sshkeys": "SSH Keys",
    "vlans": "VLANs",
    "vpcs": "VPCs",
}

T = TypeVar("T")


@dataclass
class ResponseAttribute:
    """
    Represents a single filterable attribute for a list command/action.
    """

    name: str
    type: str

    description: Optional[str]
    example: Optional[Any]

    @staticmethod
    def _format_example(attr: OpenAPIResponseAttr) -> Optional[str]:
        """
        Returns a formatted example value for the given response attribute.

        :param attr: The attribute to get an example for.

        :returns: The formatted example if it exists, else None.
        """

        example = attr.example

        if not example:
            return None

        if attr.datatype in ["object", "array"]:
            return json.dumps(attr.example)

        if isinstance(example, bool):
            return "true" if example else "false"

        return str(example)

    @classmethod
    def from_openapi(cls, attr: OpenAPIResponseAttr) -> Self:
        """
        Returns a new FilterableAttribute object initialized using values
        from the given filterable OpenAPI response attribute.

        :param attr: The OpenAPI response attribute to initialize the object with.

        :returns: The initialized object.
        """

        return cls(
            name=attr.name,
            type=_format_type(attr.datatype, item_type=attr.item_type),
            description=(
                _markdown_to_rst(attr.description)
                if attr.description != ""
                else None
            ),
            example=cls._format_example(attr),
        )


@dataclass
class Argument:
    """
    Represents a single argument for a command/action.
    """

    path: str
    required: bool
    type: str

    is_json: bool = False
    is_nullable: bool = False
    depth: int = 0
    description: Optional[str] = None
    example: Optional[Any] = None

    is_parent: bool = False
    is_child: bool = False
    parent: Optional[str] = None

    @staticmethod
    def _format_example(arg: OpenAPIRequestArg) -> Optional[str]:
        """
        Returns a formatted example value for the given argument.

        :param arg: The argument to get an example for.

        :returns: The formatted example if it exists, else None.
        """

        example = arg.example

        if not example:
            return None

        if arg.datatype == "object":
            return json.dumps(arg.example)

        if arg.datatype.startswith("array"):
            # We only want to show one entry for list arguments.
            if isinstance(example, list):
                if len(example) < 1:
                    print(
                        f"WARN: List example does not have any elements: {example}",
                        file=sys.stderr,
                    )
                    return None

                example = example[0]

        if isinstance(example, bool):
            return "true" if example else "false"

        return str(example)

    @classmethod
    def from_openapi(cls, arg: OpenAPIRequestArg) -> Self:
        """
        Returns a new Argument object initialized using values
        from the given OpenAPI request argument.

        :param arg: The OpenAPI request argument to initialize the object with.

        :returns: The initialized object.
        """

        return cls(
            path=arg.path,
            required=arg.required,
            type=_format_type(
                arg.datatype, item_type=arg.item_type, _format=arg.format
            ),
            is_json=arg.format == "json",
            is_nullable=arg.nullable,
            is_parent=arg.is_parent,
            parent=arg.parent,
            is_child=arg.is_child,
            depth=arg.depth,
            description=(
                _markdown_to_rst(arg.description)
                if arg.description != ""
                else None
            ),
            example=cls._format_example(arg),
        )


@dataclass
class Param:
    """
    Represents a single URL parameter for a command/action.
    """

    name: str
    type: str

    description: Optional[str] = None

    @classmethod
    def from_openapi(cls, param: OpenAPIOperationParameter) -> Self:
        """
        Returns a new Param object initialized using values
        from the given OpenAPI parameter.

        :param param: The OpenAPI parameter to initialize the object with.

        :returns: The initialized object.
        """

        return cls(
            name=param.name,
            type=_format_type(param.type),
            description=(
                _markdown_to_rst(param.description)
                if param.description is not None
                else None
            ),
        )


@dataclass
class FieldSection(Generic[T]):
    """
    Represents a single section of arguments.
    """

    name: str
    entries: List[T]

    @classmethod
    def from_iter(
        cls,
        data: Iterable[T],
        get_parent: Callable[[T], Optional[str]],
        sort_key: Callable[[T], Any],
    ) -> List[Self]:
        """
        Builds a list of FieldSection created from the given data using the given functions.

        :param data: The data to partition.
        :param get_parent: A function returning the parent of this entry.
        :param sort_key: A function passed into the `key` argument of the sort function.

        :returns: The built list of sections.
        """

        sections = defaultdict(lambda: [])

        for entry in data:
            parent = get_parent(entry)

            sections[parent if parent is not None else ""].append(entry)

        return sorted(
            [
                FieldSection(name=key, entries=sorted(section, key=sort_key))
                for key, section in sections.items()
            ],
            key=lambda section: section.name,
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
            action=(
                operation.action
                if isinstance(operation.action, list)
                else [operation.action]
            ),
            summary=_markdown_to_rst(operation.summary),
            description=(
                _markdown_to_rst(operation.description)
                if operation.description != ""
                else None
            ),
            usage=cls._get_usage(operation),
            api_documentation_url=operation.docs_url,
            deprecated=operation.deprecated,
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
                section.name for section in result.argument_sections
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


@dataclass
class Group:
    """
    Represents a single "group" of commands/actions as defined by the Linode API.
    """

    name: str
    pretty_name: str
    actions: List[Action]

    @classmethod
    def from_openapi(
        cls, name: str, group: Dict[str, OpenAPIOperation]
    ) -> Self:
        """
        Returns a new Group object initialized using values
        from the given name and group mapping.

        :param name: The name/key of the group.
        :param group: A mapping between action names and their corresponding OpenAPIOperations.

        :returns: The initialized object.
        """

        return cls(
            name=name,
            pretty_name=(
                GROUP_NAME_CORRECTIONS[name]
                if name in GROUP_NAME_CORRECTIONS
                else name.title().replace("-", " ")
            ),
            actions=sorted_actions_smart(
                [Action.from_openapi(action) for action in group.values()],
                key=lambda v: v.action[0],
            ),
        )


@dataclass
class Root:
    """
    The root template data structure for the Linode CLI.
    """

    groups: List[Group]

    @classmethod
    def from_cli(cls, cli: CLI) -> Self:
        """
        Returns a new Root object initialized using values
        from the given CLI.

        :param cli: The CLI to initialize the object with.

        :returns: The initialized object.
        """

        return cls(
            groups=sorted(
                [
                    Group.from_openapi(key, group)
                    for key, group in cli.ops.items()
                ],
                key=lambda v: v.name,
            ),
        )


@dataclass
class BuildMeta:
    """
    Contains metadata about a single documentation build.
    """

    cli_version: str
    api_spec_version: str
