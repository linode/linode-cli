def flatten_response(operation, response):
    """
    Given an operation and a response (JSON as a python dict) from that operation,
    flattens the response into a table as per the parsed spec data.

    :param operation: The Operation this request was made to
    :type operation: linodecli.baked.OpenAPIOperation
    :param response: The response from the API for the given operation
    :type response: dict

    :returns: The flattened response
    :rtype: list[any]
    """
    return [] # TODO
