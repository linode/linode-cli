"""
Provides various utility functions for use in baking logic.
"""

from collections import defaultdict
from typing import Any, Dict, Set, Tuple

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

    def _handle_schema(_schema: Schema):
        if _schema.properties is None:
            return

        nonlocal schema_count
        schema_count += 1

        properties.update(dict(_schema.properties))

        # Aggregate required keys and their number of usages.
        if _schema.required is not None:
            for key in _schema.required:
                required[key] += 1

    _handle_schema(schema)

    one_of = schema.oneOf or []
    any_of = schema.anyOf or []

    for entry in one_of + any_of:
        # pylint: disable=protected-access
        _handle_schema(Schema(schema.path, entry, schema._root))

    return (
        properties,
        # We only want to mark fields that are required by ALL subschema as required
        set(key for key, count in required.items() if count == schema_count),
    )
