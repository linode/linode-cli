from dataclasses import dataclass, field
from io import StringIO
from typing import Dict, List, Optional, Self

from linodecli import CLI
from linodecli.baked import OpenAPIOperation
from linodecli.baked.operation import OpenAPIOperationParameter
from linodecli.baked.request import OpenAPIRequestArg
from linodecli.baked.response import OpenAPIResponseAttr
from linodecli.documentation.util import (
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


@dataclass
class FilterableAttribute:
    """
    Represents a single filterable attribute for a list command/action.
    """

    name: str
    type: str

    description: Optional[str]

    @classmethod
    def from_openapi(cls, attr: OpenAPIResponseAttr) -> Self:
        return cls(
            name=attr.name,
            type=(
                attr.datatype
                if attr.item_type is None
                else f"{attr.datatype}[{attr.item_type}]"
            ),
            description=(
                _markdown_to_rst(attr.description)
                if attr.description != ""
                else None
            ),
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
    is_parent: bool = False
    depth: int = 0
    description: Optional[str] = None

    @classmethod
    def from_openapi(cls, arg: OpenAPIRequestArg) -> Self:
        return cls(
            path=arg.path,
            required=arg.required,
            type=(
                arg.datatype
                if arg.item_type is None
                else f"{arg.datatype}[{arg.item_type}]"
            ),
            is_json=arg.format == "json",
            is_nullable=arg.nullable,
            is_parent=arg.is_parent,
            depth=arg.depth,
            description=(
                _markdown_to_rst(arg.description)
                if arg.description != ""
                else None
            ),
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
        return cls(
            name=param.name,
            type=param.type,
            description=(
                _markdown_to_rst(param.description)
                if param.description is not None
                else None
            ),
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
    filterable_attrs: List[FilterableAttribute] = field(
        default_factory=lambda: []
    )
    arguments: List[Argument] = field(default_factory=lambda: [])

    @classmethod
    def from_openapi(cls, operation: OpenAPIOperation) -> Self:
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

        if operation.args:
            result.arguments = sorted(
                [
                    Argument.from_openapi(arg)
                    for arg in operation.args
                    if isinstance(arg, OpenAPIRequestArg)
                ],
                key=lambda arg: (not arg.required, arg.path),
            )

        if operation.method == "get" and operation.response_model.is_paginated:
            result.filterable_attrs = sorted(
                [
                    FilterableAttribute.from_openapi(attr)
                    for attr in operation.response_model.attrs
                    if attr.filterable
                ],
                key=lambda v: v.name,
            )

        result.usage = Action._get_usage(operation)

        return result

    @staticmethod
    def _get_usage(operation: OpenAPIOperation) -> str:
        usage_io = StringIO()
        operation._build_parser()[0].print_usage(file=usage_io)

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
