"""
Contains the template data for Linode CLI groups.
"""

from dataclasses import dataclass
from typing import Dict, List, Self

from linodecli.baked import OpenAPIOperation
from linodecli.documentation.template_data.action import Action
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
