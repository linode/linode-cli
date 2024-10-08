"""
Contains the template data for Linode CLI params.
"""

from dataclasses import dataclass
from typing import Optional, Self

from linodecli.baked.operation import OpenAPIOperationParameter
from linodecli.documentation.template_data.util import (
    _format_type,
    _markdown_to_rst,
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
