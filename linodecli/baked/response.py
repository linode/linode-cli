"""
Converting the processed OpenAPI Responses into something the CLI can work with
"""

from typing import Optional

from openapi3.paths import MediaType
from openapi3.schemas import Schema

from linodecli.baked.util import _aggregate_schema_properties


def _is_paginated(response):
    """
    Returns True if this operation has a paginated response
    :param response: The response we're checking
    :type response: openapi3.Response
    """
    return (
        response.schema.properties is not None
        and len(response.schema.properties) == 4
        and all(
            c in response.schema.properties
            for c in ("pages", "page", "results", "data")
        )
    )


class OpenAPIResponseAttr:
    """
    Represents a single attribute of an API response as defined by the OpenAPI spec.
    This class is given the schema node from the spec and parses out its own information
    from it.
    """

    def __init__(
        self,
        name: str,
        schema: Schema,
        prefix: Optional[str] = None,
        nested_list_depth: int = 0,
    ) -> None:
        """
        :param name: The key that held this schema in the properties list, representing
                     its name in a response.
        :type name: str
        :param schema: The schema this attribute will represent
        :type schema: openapi3.Schema
        :param prefix: The json path style prefix (dot notation) to this schema
                       in the response object
        :type prefix: str
        :param nested_list_depth: The number of nested lists this attribute is nested in.
        :type: nested_list_depth: int
        """
        #: The name of this attribute, which is the full json path to it within the schema
        self.name = name if prefix is None else prefix + "." + name

        #: If this attribute is filterable in GET requests
        self.filterable = schema.extensions.get("linode-filterable")

        #: The depth of this nested attribute in lists. This is necessary to prevent displaying
        #: list nested items in normal tables.
        self.nested_list_depth = nested_list_depth

        #: The description of this argument, for help display.  Only used for filterable attributes.
        self.description = (
            schema.description.split(".")[0] if schema.description else ""
        )

        #: No response model fields are required. This is only used for filterable attributes.
        self.required = False

        #: If this argument is Read Only
        self.read_only = schema.readOnly

        #: If this attribute should be displayed by default, and where in the output table
        #: it should be displayed
        self.display = schema.extensions.get("linode-cli-display") or 0

        #: The name of the column header for this attribute.  This is the schema's name
        #: without the full path to it
        self.column_name = name

        #: The type of data this attribute contains
        self.datatype = schema.type or "string"

        #: How we should associate values of this attribute to output colors
        self.color_map = schema.extensions.get("linode-cli-color")

        #: The type for items in this attribute, if this attribute is a list
        self.item_type = None
        if schema.type == "array":
            self.item_type = schema.items.type

    @property
    def path(self) -> str:
        """
        This is a helper for filterable fields to return the json path to this
        element in a response.

        :returns: The json path to the element in a response.
        :rtype: str
        """
        return self.name

    def _get_value(self, model):
        """
        Walk through json paths to find value

        :param model: adjusted JSON data from response
        """
        value = model
        for part in self.name.split("."):
            if (
                value is None
                or value == {}
                or isinstance(value, list)
                or part not in value
            ):
                return None

            value = value[part]
        return value

    def render_value(self, model, colorize=True):
        """
        Given the model returned from the API, returns the correctly rendered
        version of it.  This can transform text based on various rules
        configured in the spec using custom tags. Currently supported tags:

        x-linode-cli-color
          A list of key-value pairs that represent the value, and its ideal color.
          The key "default_" is used to colorize anything that is not included.
          If omitted, no color is applied.
        """
        value = self._get_value(model)
        if isinstance(value, list):
            value = ", ".join([str(c) for c in value])
        if colorize and self.color_map is not None:
            # Add color using rich tags
            value = str(value)
            color = self.color_map.get(value) or self.color_map["default_"]
            value = f"[{color}]{value}[/]"
        # Convert None value to an empty string for better display
        if value is None:
            # Prints the word None if you don't change it
            value = ""
        return value

    def get_string(self, model):
        """
        Returns a raw value from a model, cleaning up Nones and other values
        """
        value = self._get_value(model)
        if value is None:
            value = ""
        elif isinstance(value, list):
            value = " ".join([str(c) for c in value])
        else:
            value = str(value)
        return value


def _parse_response_model(schema, prefix=None, nested_list_depth=0):
    """
    Recursively parses all properties of this schema to create a flattened set of
    OpenAPIResponseAttr objects that allow the CLI to display this response in a
    terminal.
    :param schema: The schema to parse.  Every item in this schemas properties will
                   become a new OpenAPIResponseAttr instance, and this process is
                   recursive to include the properties of properties and so on.
    :type schema: openapi3.Schema
    :param nested_list_depth: The number of nested lists this attribute is nested in.
    :type: nested_list_depth: int
    :returns: The list of parsed OpenAPIResponseAttr objects representing this schema
    :rtype: List[OpenAPIResponseAttr]
    """

    if schema.type == "array":
        return _parse_response_model(
            schema.items,
            prefix=prefix,
            nested_list_depth=nested_list_depth,
        )

    attrs = []

    properties, _ = _aggregate_schema_properties(schema)

    if properties is None:
        return attrs

    for k, v in properties.items():
        pref = prefix + "." + k if prefix else k

        if (
            v.type == "object"
            and v.properties is None
            and v.additionalProperties is not None
        ):
            # This is a dictionary with arbitrary keys
            attrs.append(
                OpenAPIResponseAttr(
                    k, v, prefix=prefix, nested_list_depth=nested_list_depth
                )
            )
        elif v.type == "object":
            attrs += _parse_response_model(v, prefix=pref)
        elif v.type == "array" and v.items.type == "object":
            # Parse arrays for objects recursively and increase the nesting depth
            attrs += _parse_response_model(
                v.items,
                prefix=pref,
                nested_list_depth=nested_list_depth + 1,
            )
        else:
            # Handle any other simple types
            attrs.append(
                OpenAPIResponseAttr(
                    k, v, prefix=prefix, nested_list_depth=nested_list_depth
                )
            )

    return attrs


class OpenAPIResponse:
    """
    This object represents a single Response as defined by a MediaType in the
    responses section of an OpenAPI Operation
    """

    def __init__(self, response: MediaType) -> None:
        """
        :param response: The response's MediaType object in the OpenAPI spec,
                          corresponding to the application/json response type
        :type response: openapi3.MediaType
        """
        self.is_paginated = _is_paginated(response)

        schema_override = response.extensions.get("linode-cli-use-schema")

        if schema_override:
            override = type(response)(
                response.path, {"schema": schema_override}, response._root
            )
            override._resolve_references()
            self.attrs = _parse_response_model(override.schema)
        elif self.is_paginated:
            # for paginated responses, the model we're parsing is the item in the paginated
            # response, not the pagination envelope
            self.attrs = _parse_response_model(
                response.schema.properties["data"].items
            )
        else:
            self.attrs = _parse_response_model(response.schema)

        self.rows = response.extensions.get("linode-cli-rows")
        self.nested_list = response.extensions.get("linode-cli-nested-list")
        self.subtables = response.extensions.get("linode-cli-subtables")

    def fix_json(self, json):
        """
        Formats JSON from the API into a list of rows
        """

        if self.rows:
            return self._fix_json_rows(json)
        if self.nested_list:
            return self._fix_nested_list(json)
        # Needs to go last to handle custom schemas
        if "pages" in json:
            return json["data"]
        if not isinstance(json, list):
            json = [json]
        return json

    def _fix_json_rows(self, json):
        """
        Formats rows from openapi extension
        """
        result = []
        for c in self.rows:
            cur = json
            for part in c.split("."):
                cur = cur.get(part)
            if not cur:
                # shouldn't happen
                continue
            if isinstance(cur, list):
                result += cur
            else:
                result.append(cur)
        return result

    def _fix_nested_list(self, json):
        """
        Formats nested_list from openapi extension
        """
        if "pages" in json:
            json = json["data"]

        nested_lists = [c.strip() for c in self.nested_list.split(",")]
        result = []

        for nested_list in nested_lists:
            path_parts = nested_list.split(".")

            if not isinstance(json, list):
                json = [json]

            for cur in json:
                # Get the nested list using the path
                nlist_path = cur
                for p in path_parts:
                    nlist_path = nlist_path.get(p)
                nlist = nlist_path

                # For each item in the nested list,
                # combine the parent properties with the nested item
                for item in nlist:
                    cobj = {k: v for k, v in cur.items() if k != path_parts[0]}
                    cobj["_split"] = path_parts[-1]
                    cobj[path_parts[0]] = item
                    result.append(cobj)
        return result
