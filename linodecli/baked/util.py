from typing import Any, Dict

from openapi3.schemas import Schema


def _aggregate_schema_properties(schema: Schema) -> Dict[str, Any]:
    """
    Aggregates all properties in the given schema, accounting properties
    nested in oneOf and anyOf blocks.

    :param schema: The schema to aggregate properties from.
    :return: The aggregated properties.
    """

    result = {}

    if schema.properties is not None:
        result.update(dict(schema.properties))

    nested_schema = (schema.oneOf or []) + (schema.anyOf or [])

    for entry in nested_schema:
        entry_schema = Schema(schema.path, entry, schema._root)
        if entry_schema.properties is None:
            continue

        result.update(dict(entry_schema.properties))

    return result
