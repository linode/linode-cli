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

        self.request = None

        self.params = [
            OpenAPIOperationParameter(c) for c in params
        ]

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


        if method in ('post', 'put') and operation.requestBody:
            if 'application/json' in operation.requestBody.content:
                self.request = OpenAPIRequest(operation.requestBody.content['application/json'])
            else:
                print(
                    "WARNING: {} {} has no valid requestBody (must be application/json)!".format(
                         self.method,
                         self.url,
                    )
                )
        elif method in ('get',):
            # for get requests, self.request is all filterable fields of the response model
            if self.response_model and self.response_model.is_paginated:
                self.request = OpenAPIFilteringRequest(self.response_model)

    @property
    def args(self):
        return self.request.attrs if self.request else []
