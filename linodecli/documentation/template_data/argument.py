"""
Contains the template data for Linode CLI arguments.
"""

import json
import sys
from dataclasses import dataclass, field
from typing import Any, List, Optional, Self

from linodecli.baked.request import OpenAPIRequestArg
from linodecli.documentation.template_data.util import (
    _format_type,
    _markdown_to_rst,
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
    depth: int = 0
    description: Optional[str] = None
    example: Optional[Any] = None

    is_parent: bool = False
    is_child: bool = False
    parent: Optional[str] = None

    additional_details: List[str] = field(default_factory=lambda: [])

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

        additional_details = []

        if arg.nullable:
            additional_details.append("nullable")

        if arg.deprecated:
            additional_details.append("deprecated")

        if arg.write_only:
            additional_details.append("write-only")

        return cls(
            path=arg.path,
            required=arg.required,
            type=_format_type(
                arg.datatype, item_type=arg.item_type, _format=arg.format
            ),
            is_json=arg.format == "json",
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
            additional_details=additional_details,
        )
