"""
Contains the template data for field sections.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    List,
    Optional,
    Self,
    TypeVar,
)

T = TypeVar("T")


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
