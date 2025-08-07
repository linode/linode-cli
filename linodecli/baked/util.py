"""
Provides various utility functions for use in baking logic.
"""

import re
from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple

from openapi3.schemas import Schema


def _aggregate_schema_properties(
    schema: Schema,
) -> Tuple[Dict[str, Any], Set[str]]:
    """
    Aggregates all properties in the given schema, accounting properties
    nested in oneOf and anyOf blocks.

    :param schema: The schema to aggregate properties from.
    :return: The aggregated properties and a set containing the keys of required properties.
    """

    schema_count = 0
    properties = {}
    required = defaultdict(lambda: 0)

    def __inner(
        path: List[str],
        entry: Schema,
    ):
        if isinstance(entry, dict):
            # TODO: Figure out why this happens (openapi3 package bug?)
            # pylint: disable=protected-access
            entry = Schema(path, entry, schema._root)

        if entry.properties is None:
            # If there aren't any properties, this might be a
            # composite schema
            for composition_field in ["oneOf", "allOf", "anyOf"]:
                for i, nested_entry in enumerate(
                    getattr(entry, composition_field) or []
                ):
                    __inner(
                        schema.path + [composition_field, str(i)],
                        nested_entry,
                    )

            return

        # This is a valid option
        properties.update(entry.properties)

        nonlocal schema_count
        schema_count += 1

        for key in entry.required or []:
            required[key] += 1

    __inner(schema.path, schema)

    return (
        properties,
        # We only want to mark fields that are required by ALL subschema as required
        set(key for key, count in required.items() if count == schema_count),
    )


ESCAPED_PATH_DELIMITER_PATTERN = re.compile(r"(?<!\\)\.")


def escape_arg_segment(segment: str) -> str:
    """
    Escapes periods in a segment by prefixing them with a backslash.

    :param segment: The input string segment to escape.
    :return: The escaped segment with periods replaced by '\\.'.
    """
    return segment.replace(".", "\\.")


def unescape_arg_segment(segment: str) -> str:
    """
    Reverses the escaping of periods in a segment, turning '\\.' back into '.'.

    :param segment: The input string segment to unescape.
    :return: The unescaped segment with '\\.' replaced by '.'.
    """
    return segment.replace("\\.", ".")


def get_path_segments(path: str) -> List[str]:
    """
    Splits a path string into segments using a delimiter pattern,
    and unescapes any escaped delimiters in the resulting segments.

    :param path: The full path string to split and unescape.
    :return: A list of unescaped path segments.
    """
    return [
        unescape_arg_segment(seg)
        for seg in ESCAPED_PATH_DELIMITER_PATTERN.split(path)
    ]


def get_terminal_keys(data: Dict[str, Any]) -> List[str]:
    """
    Recursively retrieves all terminal (non-dict) keys from a nested dictionary.

    :param data: The input dictionary, possibly nested.
    :return: A list of all terminal keys (keys whose values are not dictionaries).
    """
    ret = []

    for k, v in data.items():
        if isinstance(v, dict):
            ret.extend(get_terminal_keys(v))  # recurse into nested dicts
        else:
            ret.append(k)  # terminal key

    return ret
