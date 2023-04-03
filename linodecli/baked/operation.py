from linodecli.baked.response import OpenAPIResponse
from linodecli.baked.request import OpenAPIRequest, OpenAPIFilteringRequest

class OpenAPIOperationParameter:
    """
    A parameter is a variable element of the URL path, generally an ID or slug
    """
    def __init__(self, parameter):
        """
        :param parameter: The Parameter object this is parsing values from
        :type parameter: openapi3.Parameter
        """
        self.name = parameter.name
        self.type = parameter.schema.type

    def __repr__(self):
        return "<OpenAPIOperationParameter {}>".format(self.name)

class OpenAPIOperation:
    """
    A wrapper class for information parsed from the OpenAPI spec for a single operation.
    This is the class that should be pickled when building the CLI.
    """

    def __init__(self, operation, method, params):
        """
        Wraps an openapi3.Operation object and handles pulling out values relevant
        to the Linode CLI.
        .. note::
           This function runs _before pickling!  As such, this is the only place
           where the OpenAPI3 objects can be accessed safely (as they are not
           usable when unpickled!)
        """
        self.method = method

        server = operation.servers[0].url if operation.servers else operation._root.servers[0].url
        self.url = server + operation.path[-2]

        self.summary = operation.summary
        self.description = operation.description.split(".")[0]
        self.responses = {}
        self.request = None
        self.params = [
            OpenAPIOperationParameter(c) for c in params
        ]

        # required_fields = request_schema.required
        # allowed_defaults = method_spec.extensions[ext['defaults']] or None

        # use_servers = (
        #     [c.url for c in spec.servers]
        #     if hasattr(method_spec, 'servers')
        #     else default_servers
        # )

        docs_url = None
        tags = method_spec.tags
        if tags is not None and len(tags) > 0 and len(summary) > 0:
            tag_path = self._flatten_url_path(tags[0])
            summary_path = self._flatten_url_path(summary)
            docs_url = f"https://www.linode.com/docs/api/{tag_path}/#{summary_path}"

        self.response_model = None

        if ('200' in operation.responses
            and 'application/json' in operation.responses['200'].content):
            self.response_model = OpenAPIResponse(
                    operation.responses['200'].content['application/json'])

        if method in ('post', 'put') and operation.requestBody:
            if 'application/json' in operation.requestBody.content:
                self.request = OpenAPIRequest(operation.requestBody.content['application/json'])
        elif method in ('get',):
            # for get requests, self.request is all filterable fields of the response model
            if self.response_model and self.response_model.is_paginated:
                self.request = OpenAPIFilteringRequest(self.response_model)

    @property
    def args(self):
        return self.request.attrs if self.request else []
        self.method = method

    @staticmethod
    def _flatten_url_path(tag):
        new_tag = tag.lower()
        new_tag = re.sub(r"[^a-z ]", "", new_tag).replace(" ", "-")
        return new_tag
