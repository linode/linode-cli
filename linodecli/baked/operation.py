"""
CLI Operation logic
"""
import argparse
import glob
import json
import platform
import re
import sys
from getpass import getpass
from os import environ, path
from typing import List, Tuple

from openapi3.paths import Operation

from linodecli.baked.request import OpenAPIFilteringRequest, OpenAPIRequest
from linodecli.baked.response import OpenAPIResponse
from linodecli.overrides import OUTPUT_OVERRIDES


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


# pylint: disable=too-few-public-methods
class ExplicitNullValue:
    """
    A special type class used to explicitly pass null values to the API.
    """


def wrap_parse_nullable_value(arg_type):
    """
    A helper function to parse `null` as None for nullable CLI args.
    This is intended to be called and passed to the `type=` kwarg for ArgumentParser.add_argument.
    """

    def type_func(value):
        if not value:
            return None

        if value == "null":
            return ExplicitNullValue()

        return TYPES[arg_type](value)

    return type_func


class ArrayAction(argparse.Action):
    """
    This action is intended to be used only with array arguments.
    This purpose of this action is to allow users to specify explicitly
    empty lists using a singular "[]" argument value.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, [])

        output_list = getattr(namespace, self.dest)

        # If the output list is empty and the user specifies a []
        # argument, keep the list empty
        if values == "[]" and len(output_list) < 1:
            return

        output_list.append(values)


class ListArgumentAction(argparse.Action):
    """
    This action is intended to be used only with list arguments.
    Its purpose is to aggregate adjacent object fields and produce consistent
    lists in the output namespace.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, [])

        dest_list = getattr(namespace, self.dest)
        dest_length = len(dest_list)
        dest_parent = self.dest.split(".")[:-1]

        # If this isn't a nested structure,
        # append and return early
        if len(dest_parent) < 1:
            dest_list.append(values)
            return

        # A list of adjacent fields
        adjacent_keys = [
            k
            for k in vars(namespace).keys()
            if k.split(".")[:-1] == dest_parent
        ]

        # Let's populate adjacent fields ahead of time
        for k in adjacent_keys:
            if getattr(namespace, k) is None:
                setattr(namespace, k, [])

        adjacent_items = {k: getattr(namespace, k) for k in adjacent_keys}

        # Find the deepest field so we can know if
        # we're starting a new object.
        deepest_length = max(len(x) for x in adjacent_items.values())

        # If we're creating a new list object, append
        # None to every non-populated field.
        if dest_length >= deepest_length:
            for k, item in adjacent_items.items():
                if k == self.dest:
                    continue

                if len(item) < dest_length:
                    item.append(None)

        dest_list.append(values)


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
        return f"<OpenAPIOperationParameter {self.name}>"


class OpenAPIOperation:
    """
    A wrapper class for information parsed from the OpenAPI spec for a single operation.
    This is the class that should be pickled when building the CLI.
    """

    def __init__(self, command, operation: Operation, method, params):
        """
        Wraps an openapi3.Operation object and handles pulling out values relevant
        to the Linode CLI.
        .. note::
           This function runs _before pickling!  As such, this is the only place
           where the OpenAPI3 objects can be accessed safely (as they are not
           usable when unpickled!)
        """
        self.request = None
        self.responses = {}
        self.response_model = None
        self.allowed_defaults = None

        if (
            "200" in operation.responses
            and "application/json" in operation.responses["200"].content
        ):
            self.response_model = OpenAPIResponse(
                operation.responses["200"].content["application/json"]
            )

        if method in ("post", "put") and operation.requestBody:
            if "application/json" in operation.requestBody.content:
                self.request = OpenAPIRequest(
                    operation.requestBody.content["application/json"]
                )
                self.required_fields = self.request.required
                self.allowed_defaults = operation.requestBody.extensions.get(
                    "linode-cli-allowed-defaults"
                )
        elif method in ("get",):
            # for get requests, self.request is all filterable fields of the response model
            if self.response_model and self.response_model.is_paginated:
                self.request = OpenAPIFilteringRequest(self.response_model)

        self.method = method
        self.command = command

        action = operation.extensions.get(
            "linode-cli-action", operation.operationId
        )
        if isinstance(action, list):
            self.action_aliases = action[1:]
            self.action = action[0]
        else:
            self.action_aliases = {}
            self.action = action

        self.summary = operation.summary
        self.description = operation.description.split(".")[0]
        self.params = [OpenAPIOperationParameter(c) for c in params]

        # These fields must be stored separately
        # to allow them to be easily modified
        # at runtime.
        self.url_base = (
            operation.servers[0].url
            if operation.servers
            else operation._root.servers[0].url
        )

        self.url_path = operation.path[-2]

        self.url = self.url_base + self.url_path

        docs_url = None
        tags = operation.tags
        if tags is not None and len(tags) > 0 and len(operation.summary) > 0:
            tag_path = self._flatten_url_path(tags[0])
            summary_path = self._flatten_url_path(operation.summary)
            docs_url = (
                f"https://www.linode.com/docs/api/{tag_path}/#{summary_path}"
            )
        self.docs_url = docs_url

    @property
    def args(self):
        """
        Return a list of attributes from the request schema
        """
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
        if self.response_model.attrs == []:
            return

        override = OUTPUT_OVERRIDES.get(
            (self.command, self.action, handler.mode)
        )
        if override is not None and not override(self, handler, json):
            return

        json = self.response_model.fix_json(json)
        handler.print_response(self.response_model, json)

    def _add_args_filter(self, parser):
        # build args for filtering
        filterable_args = []
        for attr in self.response_model.attrs:
            if not attr.filterable:
                continue

            expected_type = TYPES[attr.datatype]
            filterable_args.append(attr.name)
            if expected_type == list:
                parser.add_argument(
                    "--" + attr.name,
                    type=TYPES[attr.item_type],
                    metavar=attr.name,
                    action="append",
                    nargs="?",
                )
            else:
                parser.add_argument(
                    "--" + attr.name,
                    type=expected_type,
                    metavar=attr.name,
                )
        # Add --order-by and --order argument
        parser.add_argument(
            "--order-by",
            choices=filterable_args,
            help="Attribute to order the results by - must be filterable.",
            required="--order" in sys.argv,
        )

        parser.add_argument(
            "--order",
            choices=["asc", "desc"],
            default="asc",
            help="Either “asc” or “desc”. Defaults to “asc”. Requires +order_by",
        )

    def _add_args_post_put(self, parser) -> List[Tuple[str, str]]:
        list_items = []

        # build args for body JSON
        for arg in self.args:
            if arg.read_only:
                continue

            arg_type = (
                arg.item_type if arg.datatype == "array" else arg.datatype
            )
            arg_type_handler = TYPES[arg_type]

            if arg.nullable:
                arg_type_handler = wrap_parse_nullable_value(arg_type)

            if arg.datatype == "array":
                # special handling for input arrays
                parser.add_argument(
                    "--" + arg.path,
                    metavar=arg.name,
                    action=ArrayAction,
                    type=arg_type_handler,
                )
            elif arg.list_item:
                parser.add_argument(
                    "--" + arg.path,
                    metavar=arg.name,
                    action=ListArgumentAction,
                    type=arg_type_handler,
                )
                list_items.append((arg.path, arg.prefix))
            else:
                if arg.datatype == "string" and arg.format == "password":
                    # special case - password input
                    parser.add_argument(
                        "--" + arg.path,
                        nargs="?",
                        action=PasswordPromptAction,
                    )
                elif arg.datatype == "string" and arg.format in (
                    "file",
                    "ssl-cert",
                    "ssl-key",
                ):
                    parser.add_argument(
                        "--" + arg.path,
                        metavar=arg.name,
                        action=OptionalFromFileAction,
                        type=arg_type_handler,
                    )
                else:
                    parser.add_argument(
                        "--" + arg.path,
                        metavar=arg.name,
                        type=arg_type_handler,
                    )

        return list_items

    @staticmethod
    def _handle_list_items(
        list_items,
        parsed,
    ):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
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

    def parse_args(self, args):
        """
        Given sys.argv after the operation name, parse args based on the params
        and args of this operation
        """

        #  build an argparse
        parser = argparse.ArgumentParser(
            prog=f"linode-cli {self.command} {self.action}",
            description=self.summary,
        )
        for param in self.params:
            parser.add_argument(
                param.name, metavar=param.name, type=TYPES[param.type]
            )

        list_items = []

        if self.method == "get":
            self._add_args_filter(parser)
        elif self.method in ("post", "put"):
            list_items = self._add_args_post_put(parser)

        return self._handle_list_items(list_items, parser.parse_args(args))
