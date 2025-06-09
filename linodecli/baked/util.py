"""
Provides various utility functions for use in baking logic.
"""

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
