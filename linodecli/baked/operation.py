import re
import json
import glob
import argparse
import platform
from getpass import getpass
from os import environ, path

from linodecli.baked.response import OpenAPIResponse
from linodecli.baked.request import OpenAPIRequest, OpenAPIFilteringRequest


def parse_boolean(value):
    """
    A helper to allow accepting booleans in from argparse.  This is intended to
    be passed to the `type=` kwarg for ArgumentParser.add_argument.
    """
    if value.lower() in ("yes", "true", "y", "1"):
        return True
    if value.lower() in ("no", "false", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Expected a boolean value")


def parse_dict(value):
    """
    A helper function to decode incoming JSON data as python dicts.  This is
    intended to be passed to the `type=` kwarg for ArgumentParaser.add_argument.
    """
    if not isinstance(value, str):
        raise argparse.ArgumentTypeError("Expected a JSON string")
    try:
        return json.loads(value)
    except Exception as e:
        raise argparse.ArgumentTypeError("Expected a JSON string") from e

TYPES = {
    "string": str,
    "integer": int,
    "boolean": parse_boolean,
    "array": list,
    "object": parse_dict,
    "number": float,
}

class PasswordPromptAction(argparse.Action):
    """
    A special argparse Action to handle prompting for password.  Also accepts
    passwords on the terminal to allow for backwards-compatible behavior.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        # if not provided on the command line, pull from the environment if it
        # exists at this key
        environ_key = f"LINODE_CLI_{self.dest.upper()}"

        if values:
            if isinstance(values, str):
                password = values
            else:
                raise argparse.ArgumentTypeError(
                    "Expected a string (or leave blank for prompt)"
                )
        elif environ_key in environ:
            password = environ.get(environ_key)
        else:
            prompt = f"Value for {self.dest}: "
            password = getpass(prompt)
        setattr(namespace, self.dest, password)


class OptionalFromFileAction(argparse.Action):
    """
    A special action for handling loading a value from a file.  This will
    attempt to load the value from a file if the value looks like a path and
    the file exists, otherwise it will fall back to using the provided value.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        if isinstance(values, str):
            input_path = path.expanduser(values)

            # Windows doesn't natively expand globs, so we should implement it here
            if platform.system() == "Windows" and "*" in input_path:
                results = glob.glob(input_path, recursive=True)

                if len(results) < 1:
                    raise argparse.ArgumentError(
                        self, f"File matching pattern {input_path} not found"
                    )

                input_path = results[0]

            if path.exists(input_path) and path.isfile(input_path):
                with open(input_path, encoding="utf-8") as f:
                    data = f.read()
                setattr(namespace, self.dest, data)
            else:
                setattr(namespace, self.dest, values)
        else:
            raise argparse.ArgumentTypeError("Expected a string")

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
        # TODO: fix
        self.command = None
        self.action = None

        # required_fields = request_schema.required
        # allowed_defaults = method_spec.extensions[ext['defaults']] or None

        # use_servers = (
        #     [c.url for c in spec.servers]
        #     if hasattr(method_spec, 'servers')
        #     else default_servers
        # )

        # docs_url = None
        # tags = method_spec.tags
        # if tags is not None and len(tags) > 0 and len(summary) > 0:
        #     tag_path = self._flatten_url_path(tags[0])
        #     summary_path = self._flatten_url_path(summary)
        #     docs_url = f"https://www.linode.com/docs/api/{tag_path}/#{summary_path}"

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

    @staticmethod
    def _flatten_url_path(tag):
        new_tag = tag.lower()
        new_tag = re.sub(r"[^a-z ]", "", new_tag).replace(" ", "-")
        return new_tag

    def process_response_json(
        self, json, handler
    ):  # pylint: disable=redefined-outer-name
        """
        Processes the response as JSON and prints
        """
        if self.response_model is None:
            return

        json = self.response_model.fix_json(json)

        handler.print(self.response_model, json)

    def parse_args(
        self, args
    ):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """
        Given sys.argv after the operation name, parse args based on the params
        and args of this operation
        """
        list_items = []

        #  build an argparse
        parser = argparse.ArgumentParser(
            prog=f"linode-cli {self.command} {self.action}",
            description=self.summary,
        )
        for param in self.params:
            parser.add_argument(
                param.name, metavar=param.name, type=TYPES[param.param_type]
            )

        if self.method == "get":
            # build args for filtering
            for attr in self.response_model.attrs:
                if attr.filterable:
                    expected_type = TYPES[attr.datatype]
                    if expected_type == list:
                        parser.add_argument(
                            "--" + attr.name,
                            type=TYPES[attr.item_type],
                            metavar=attr.name,
                            nargs="?",
                        )
                    else:
                        parser.add_argument(
                            "--" + attr.name,
                            type=expected_type,
                            metavar=attr.name,
                        )

        elif self.method in ("post", "put"):
            # build args for body JSON
            for arg in self.args:
                if arg.arg_type == "array":
                    # special handling for input arrays
                    parser.add_argument(
                        "--" + arg.path,
                        metavar=arg.name,
                        action="append",
                        type=TYPES[arg.arg_item_type],
                    )
                elif arg.list_item is not None:
                    parser.add_argument(
                        "--" + arg.path,
                        metavar=arg.name,
                        action="append",
                        type=TYPES[arg.arg_type],
                    )
                    list_items.append((arg.path, arg.list_item))
                else:
                    if (
                        arg.arg_type == "string"
                        and arg.arg_format == "password"
                    ):
                        # special case - password input
                        parser.add_argument(
                            "--" + arg.path,
                            nargs="?",
                            action=PasswordPromptAction,
                        )
                    elif arg.arg_type == "string" and arg.arg_format in (
                        "file",
                        "ssl-cert",
                        "ssl-key",
                    ):
                        parser.add_argument(
                            "--" + arg.path,
                            metavar=arg.name,
                            action=OptionalFromFileAction,
                            type=TYPES[arg.arg_type],
                        )
                    else:
                        parser.add_argument(
                            "--" + arg.path,
                            metavar=arg.name,
                            type=TYPES[arg.arg_type],
                        )

        parsed = parser.parse_args(args)
        lists = {}
        # group list items as expected
        for arg_name, list_name in list_items:
            item_name = arg_name.split(list_name)[1][1:]
            if hasattr(parsed, arg_name):
                val = getattr(parsed, arg_name) or []
                if not val:
                    continue
                if list_name not in lists:
                    new_list = [{item_name: c} for c in val]
                    lists[list_name] = new_list
                else:
                    update_list = lists[list_name]
                    for obj, item in zip(update_list, val):
                        obj[item_name] = item

        # break out list items with periods in their name into objects.  This
        # allows supporting nested lists
        for _, cur_list in lists.items():
            # for each list in lists
            for item in cur_list:
                # for each item in the list (these are dicts)
                new_dicts = {}
                remove_keys = []
                for k, v in item.items():
                    # if there's a period in the key, split it into a dict and
                    # possibly merge it with a dict that came from a prior split
                    #
                    # XXX: This only supports one layer of nested dicts in lists
                    if "." in k:
                        dict_key, key = k.split(".", 1)
                        if dict_key in new_dicts:
                            new_dicts[dict_key][key] = v
                        else:
                            new_dicts[dict_key] = {key: v}
                        remove_keys.append(k)

                # remove the original keys
                for key in remove_keys:
                    del item[key]
                # and add the combined keys
                item.update(new_dicts)

        # don't send along empty lists
        to_delete = []
        for k, v in lists.items():
            if len(v) == 0:
                to_delete.append(k)

        for c in to_delete:
            del lists[c]

        if lists:
            parsed = vars(parsed)
            parsed.update(lists)
            for name, _ in list_items:
                del parsed[name]
            parsed = argparse.Namespace(**parsed)

        return parsed