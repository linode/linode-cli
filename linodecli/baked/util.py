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

    if schema.oneOf is not None:
        result.update(dict(schema.oneOf))

    if schema.anyOf is not None:
        result.update(dict(schema.anyOf))

    return result
