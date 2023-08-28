"""
Request details for a CLI Operation
"""


class OpenAPIRequestArg:
    """
    A single argument to a request as defined by a Schema in the OpenAPI spec
    """

    def __init__(
        self, name, schema, required, prefix=None, list_item=False
    ):  # pylint: disable=too-many-arguments
        """
        Parses a single Schema node into a argument the CLI can use when making
        requests.
        :param name: The name of this argument
        :type name: str
        :param schema: The schema we're parsing data from
        :type schema: openapi3.Schema
        :param required: If this argument is required by the schema
        :type required: bool
        :param prefix: The prefix for this arg's path, used in the actual argument
                       to the CLI to ensure unique arg names
        :type prefix: str
        """
        #: The name of this argument, mostly used for display and docs
        self.name = name

        #: The path for this argument, which is full json path for its place in
        #: the larger response model
        self.path = prefix + "." + name if prefix else name

        #: The description of this argument, for help display
        self.description = (
            schema.description.split(".")[0] if schema.description else ""
        )

        #: If this argument is required for requests
        self.required = required

        #: If this argument is Read Only
        self.read_only = schema.readOnly

        #: The format of data this argument accepts; typically ignored, but can be
        #: either "json" to signal that we should not parse further spec here and just
        #: accept arbitrary json, or "file" to signal to the CLI to attempt to resolve
        #: the string passed in by the end user as a file path and send the entire file
        self.format = (
            schema.extensions.get("linode-cli-format") or schema.format or None
        )

        #: The type accepted for this argument. This will ultimately determine what
        #: we accept in the ArgumentParser
        self.datatype = (
            "object" if self.format == "json" else schema.type or "string"
        )

        #: The type of item accepted in this list; if None, this is not a list
        self.item_type = None

        #: Whether the argument is a field in a nested list.
        self.list_item = list_item

        #: The path of the path element in the schema.
        self.prefix = prefix

        #: Whether null is an acceptable value for this attribute
        self.nullable = schema.nullable

        # handle the type for list values if this is an array
        if self.datatype == "array" and schema.items:
            self.item_type = schema.items.type

        # make sure we're not doing something wrong
        if self.item_type == "object":
            raise ValueError(
                "Invalid OpenAPIRequestArg creation; created arg for base object "
                "instead of object's properties!  This is a programming error."
            )


def _parse_request_model(schema, prefix=None, list_of_objects=False):
    """
    Parses a schema into a list of OpenAPIRequest objects
    :param schema: The schema to parse as a request model
    :type schema: openapi3.Schema
    :param prefix: The prefix to add to all keys in this schema, as a json path
    :type prefix: str
    :param list_of_object: If true, this schema is the schema for items of a list.
                           This is a complex case for the CLI, where lists of objects
                           must be associated in a way that allows proper matching
                           of inputs on the command line.
    :type list_of_objects: bool
    :returns: The flattened request model, as a list
    :rtype: list[OpenAPIRequestArg]
    """
    args = []

    if schema.properties is not None:
        for k, v in schema.properties.items():
            if v.type == "object" and not v.readOnly and v.properties:
                # nested objects receive a prefix and are otherwise parsed normally
                pref = prefix + "." + k if prefix else k
                args += _parse_request_model(v, prefix=pref)
            elif (
                v.type == "array"
                and v.items
                and v.items.type == "object"
                and v.extensions.get("linode-cli-format") != "json"
            ):
                # handle lists of objects as a special case, where each property
                # of the object in the list is its own argument
                pref = prefix + "." + k if prefix else k
                args += _parse_request_model(
                    v.items, prefix=pref, list_of_objects=True
                )
            else:
                # required fields are defined in the schema above the property, so
                # we have to check here if required fields are defined/if this key
                # is among them and pass it into the OpenAPIRequestArg class.
                required = False
                if schema.required:
                    required = k in schema.required
                args.append(
                    OpenAPIRequestArg(
                        k, v, required, prefix=prefix, list_item=list_of_objects
                    )
                )

    return args


class OpenAPIRequest:
    """
    This class represent the request object we send in to an API endpoint based
    on the MediaType object of a requestBody portion of an OpenAPI Operation
    """

    def __init__(self, request):
        """
        :param request: The request's MediaType object in the OpenAPI spec,
                        corresponding to the application/json data the endpoint
                        accepts.
        :type request: openapi3.MediaType
        """
        self.required = request.schema.required
        schema_override = request.extensions.get("linode-cli-use-schema")
        if schema_override:
            override = type(request)(
                request.path, {"schema": schema_override}, request._root
            )
            override._resolve_references()
            self.attrs = _parse_request_model(override.schema)
        else:
            self.attrs = _parse_request_model(request.schema)


class OpenAPIFilteringRequest:
    """
    This class represents the X-Filter header we send for GET requests based on
    the x-linode-filterable spec extension defined in the schema of the model
    for 200 Response from an endpoint.  This only applies to paginated collection
    endpoints where filters are accepted.
    """

    def __init__(self, response_model):
        """
        :param response_model: The parsed response model whose properties may be
                               filterable.
                               The provided response model **must** be a paginated
                               response, or else the call to this constructor would
                               be invalid (as only paginated collections may be filtered).
        :type response_model: linodecli.baked.response.OpenAPIResponse
        """
        # enforce the above requirements for parameters to this constructor
        if not response_model.is_paginated:
            raise ValueError(
                f"Non-paginated schema {response_model.schema} send to "
                "OpenAPIFilteringRequest constructor!"
            )

        # actually parse out what we can filter by
        self.attrs = [c for c in response_model.attrs if c.filterable]
