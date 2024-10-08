"""
Contains root template data for the Linode CLI.
"""

from dataclasses import dataclass
from typing import List, Self

from linodecli.cli import CLI
from linodecli.documentation.template_data.group import Group


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
