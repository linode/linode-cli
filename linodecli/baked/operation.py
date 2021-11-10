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


class OpenAPIOperation:
    """
    A wrapper class for information parsed from the OpenAPI spec for a single operation.
    This is the class that should be pickled when building the CLI.
    """
    def __init__(self, operation, method):
        """
        Wraps an openapi3.Operation object and handles pulling out values relevant
        to the Linode CLI.

        .. note::
           This function runs _before pickling!  As such, this is the only place
           where the OpenAPI3 objects can be accessed safely (as they are not
           usable when unpickled!)
        """
        #: The method to use when invoking this operation
        self.method = method

        server = operation.servers[0].url if operation.servers else operation._root.servers[0].url
        #: The URL to call to invoke this operation
        self.url = server + operation.path[-2]

        #: This operation's summary for the help screen
        self.summary = operation.summary
        #: This operation's long description for the help screen
        self.description = operation.description.split(".")[0]

        #: The responses this operation understands
        self.responses = {}

        #TODO - add these
        #self.args = args
        #self.params = params

        #for code, data in operation.responses.items():
        #    if "application/json" in data.content:
        #        self.responses[code] = OpenAPIResponse(data.content['application/json'])
        #    else:
        #        print(
        #            "WARNING: Operation {} {} has invalid response for code {} (only accepts application/json)".format(
        #                self.method,
        #                self.url,
        #                code,
        #        ))


        #self.response_model = self.responses['200'] if '200' in self.responses else None

        self.response_model = None

        if '200' in operation.responses and 'application/json' in operation.responses['200'].content:
            self.response_model = OpenAPIResponse(operation.responses['200'].content['application/json'])


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
        self.filterable = schema.extensions.get("x-linode-filterable")

        #: If this attribute should be displayed by default, and where in the output table
        #: it should be displayed
        self.display = schema.extensions.get("x-linode-cli-display")

        #: The name of the column header for this attribute.  This is the schema's name
        #: without the full path to it
        self.column_name = name

        #: The type of data this attribute contains
        self.datatype = schema.type

        #: How we should associate values of this attribute to output colors
        self.color_map = schema.extensions.get("x-linode-cli-color")

        #: The type for items in this attribute, if this attribute is a list
        self.item_type = None
        if schema.type == "array":
            print("My name is {} and my path is {}".format(name, schema.path))
            self.item_type = schema.items.type


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
        print("Lookiung at {}".format(schema))
        print("It is of type {}".format(type(schema)))
        print("It has path {}".format(schema.path))
        for k, v in schema.properties.items():
            if v.type == "object":
                prefix = prefix + "." + k if prefix else k
                attrs += _parse_response_model(v, prefix=prefix)
            else:
                print("making model for {} {}".format(k, v))
                attrs.append(
                    OpenAPIResponseAttr(k, v, prefix=prefix)
                )

    return attrs


class OpenAPIResponse:
    def __init__(self, response):
        """
        :param response: The response's MediaType object in the OpenAPI spec,
                          corresponding to the application/json response type
        :type response: openapi3.MediaType
        """
        self.is_paginated = _is_paginated(response)

        schema_override = response.extensions.get("x-linode-cli-use-schema")
        if schema_override:
            self.attrs = _parse_response_model(schema_override)
        else:
            self.attrs = _parse_response_model(response.schema)
        self.rows = response.schema.extensions.get("x-linode-cli-rows")
        self.nested_list = response.extensions.get("x-linode-cli-nested-list")
