class OpenAPIRequestArg:
    """
    A single argument to a request as defined by a Schema in the OpenAPI spec
    """
    def __init__(self, name, schema, prefix=None):
        """
        Parses a single Schema node into a argument the CLI can use when making
        requests.

        :param name: The name of this argument
        :type name: str
        :param schema: The schema we're parsing data from
        :type schema: openapi3.Schema
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
        self.desc = schema.description

        #: The format of data this argument accepts; typically ignored, but can be
        #: either "json" to signal that we should not parse further spec here and just
        #: accept arbitrary json, or "file" to signal to the CLI to attempt to resolve
        #: the string passed in by the end user as a file path and send the entire file
        self.format = schema.extensions.get("x-linode-cli-format") or schema.format or None

        #: The type accepted for this argument. This will ultimately determine what
        #: we accept in the ArgumentParser
        self.type = "object" if self.format == "json" else schema.type

        #: The type of item accepted in this list; if None, this is not a list
        self.item_type = None

        # handle the type for list values if this is an array
        if self.type == "array" and schema.items:
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
    """
    args = []

    if schema.properties is not None:
        for k, v in schema.properties.items():
            print("Looking at {} {}".format(k, v))
            if v.type == "object":
                # nested objects receive a prefix and are otherwise parsed normally
                pref = prefix + "." + k if prefix else k
                args += _parse_request_model(v, prefix=pref)
            elif v.type == "array" and v.items and v.items.type == "object":
                # handle lists of objects as a special case, where each property
                # of the object in the list is its own argument
                pref = prefix + "." + k if prefix else k
                args += _parse_request_model(v.items, prefix=pref, list_of_objects=True)
            else:
                args.append(OpenAPIRequestArg(k, v, prefix=prefix))

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
        schema_override = request.extensions.get("x-linode-cli-use-schema")
        if schema_override:
            self.attrs = _parse_request_model(schema_override)
        else:
            self.attrs = _parse_request_model(request.schema)
