import math
from typing import Callable, Dict


def get_filter_map() -> Dict[str, Callable]:
    """
    Returns a map used to define filters used by the documentation template.

    :returns: The filter map.
    """

    return {
        "truncate_middle": _filter_truncate_middle,
    }


def _filter_truncate_middle(
    target: str, length: int = 64, middle: str = "..."
) -> str:
    """
    Filter to truncate the given string with a centered truncation.

    For example::

        {{ "totruncate" | truncate_middle(length=6) }} # tot...ate

    :param target: The string to truncate.
    :param length: The maximum length of the string, not including truncation characters.
    :param middle: The string to use in between the two string segments.

    :returns: The truncated string.
    """
    target_length = len(target)

    if target_length <= length:
        return target

    target_length_half = math.ceil(target_length / 2)
    offset = math.ceil((target_length - length) / 2)

    return f"{target[:target_length_half-offset]}{middle}{target[target_length_half+offset:]}"
