"""
Contains the template data for Linode CLI response attributes.
"""

import json
from dataclasses import dataclass
from typing import Any, Optional, Self

from linodecli.baked.response import OpenAPIResponseAttr
from linodecli.documentation.template_data.util import (
    _format_type,
    _markdown_to_rst,
)


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
