def _is_paginated(response):
    """
    Returns True if this operation has a paginated response

    :param response: The response we're checking
    :type response: openapi3.Response
    """
    return (
        response.schema.properties is not None and
        len(response.schema.properties) == 4 and
        all([c in response.schema.properties for c in ('pages', 'page', 'results', 'data')])
    )


class OpenAPIResponseAttr:
    """
    Represents a single attribute of an API response as defined by the OpenAPI spec.
    This class is given the schema node from the spec and parses out its own information
    from it.
    """
    def __init__(self, name, schema, prefix=None):
        """
        :param name: The key that held this schema in the properties list, representing
                     its name in a response.
        :type name: str
        :param schema: The schema this attribute will represent
        :type schema: openapi3.Schema
        :param prefix: The json path style prefix (dot notation) to this schema
                       in the response object
        :type prefix: str
        """
        #: The name of this attribute, which is the full json path to it within the schema
        self.name = name if prefix is None else prefix + "." + name

        #: TODO: Not sure what this is for
        self.value = None

        #: If this attribute is filterable in GET requests
        self.filterable = schema.extensions.get("linode-filterable")

        #: The description of this argument, for help display.  Only used for filterable attributes.
        self.description = schema.description.split(".")[0] if schema.description else ""

        #: No response model fields are required. This is only used for filterable attributes.
        self.required = False

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
            print("My name is {} and my path is {}".format(name, schema.path))
            self.item_type = schema.items.type

    @property
    def path(self):
        """
        This is a helper for filterable fields to return the json path to this
        element in a response.
        """
        return self.name


def _parse_response_model(schema, prefix=None):
    """
    Recursively parses all properties of this schema to create a flattened set of
    OpenAPIResponseAttr objects that allow the CLI to display this response in a
    terminal.

    :param schema: The schema to parse.  Every item in this schemas properties will
                   become a new OpenAPIResponseAttr instance, and this process is
                   recursive to include the properties of properties and so on.
    :type schema: openapi3.Schema

    :returns: The list of parsed OpenAPIResponseAttr objects representing this schema
    :rtype: List[OpenAPIResponseAttr]
    """
    attrs = []

    if schema.properties is not None:
        for k, v in schema.properties.items():
            if v.type == "object":
                prefix = prefix + "." + k if prefix else k
                attrs += _parse_response_model(v, prefix=prefix)
            else:
                attrs.append(
                    OpenAPIResponseAttr(k, v, prefix=prefix)
                )

    return attrs


class OpenAPIResponse:
    """
    This object represents a single Response as defined by a MediaType in the
    responses section of an OpenAPI Operation
    """
    def __init__(self, response):
        """
        :param response: The response's MediaType object in the OpenAPI spec,
                          corresponding to the application/json response type
        :type response: openapi3.MediaType
        """
        self.is_paginated = _is_paginated(response)

        schema_override = response.extensions.get("linode-cli-use-schema")
        #TODO: To alleviate the below, we may consider changing how the x-linode-cli-use-schema
        #TODO: works; maybe instead of defining a freeform schema, it must be a ref pointing to
        #TODO: a schema in #/components/schemas?
        if schema_override and False: # TODO - schema overrides are dicts right now
            self.attrs = _parse_response_model(schema_override)
        elif self.is_paginated:
            # for paginated responses, the model we're parsing is the item in the paginated
            # response, not the pagination envelope
            self.attrs = _parse_response_model(response.schema.properties['data'].items)
        else:
            self.attrs = _parse_response_model(response.schema)
        self.rows = response.schema.extensions.get("linode-cli-rows")
        self.nested_list = response.extensions.get("linode-cli-nested-list")
