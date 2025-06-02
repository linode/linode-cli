"""
CLI Operation logic
"""

import argparse
import glob
import json
import logging
import platform
import re
import sys
from collections import defaultdict
from getpass import getpass
from os import environ, path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import openapi3.paths
from openapi3.paths import Operation, Parameter

from linodecli.baked.parsing import simplify_description
from linodecli.baked.request import (
    OpenAPIFilteringRequest,
    OpenAPIRequest,
    OpenAPIRequestArg,
)
from linodecli.baked.response import OpenAPIResponse
from linodecli.baked.util import unescape_arg_segment
from linodecli.exit_codes import ExitCodes
from linodecli.output.output_handler import OutputHandler
from linodecli.overrides import OUTPUT_OVERRIDES


def parse_boolean(value: str) -> bool:
    """
    A helper to allow accepting booleans in from argparse.  This is intended to
    be passed to the `type=` kwarg for ArgumentParser.add_argument.

    :param value: The value to be parsed into boolean.
    :type value: str

    :returns: The boolean value of the input.
    :rtype: bool
    """
    if value.lower() in ("yes", "true", "y", "1"):
        return True
    if value.lower() in ("no", "false", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Expected a boolean value")


def parse_dict(
    value: str,
) -> Union[Dict[str, Any], "ExplicitEmptyDictValue", "ExplicitEmptyListValue"]:
    """
    A helper function to decode incoming JSON data as python dicts.  This is
    intended to be passed to the `type=` kwarg for ArgumentParaser.add_argument.

    :param value: The json string to be parsed into dict.
    :type value: str

    :returns: The dict value of the input.
    :rtype: dict, ExplicitEmptyDictValue, or ExplicitEmptyListValue
    """
    if not isinstance(value, str):
        raise argparse.ArgumentTypeError("Expected a JSON string")

    try:
        result = json.loads(value)
    except Exception as e:
        raise argparse.ArgumentTypeError("Expected a JSON string") from e

    # This is necessary because empty dicts and lists are excluded from requests
    # by default, but we still want to support user-defined empty dict
    # strings. This is particularly helpful when updating LKE node pool
    # labels and taints.
    if isinstance(result, dict) and result == {}:
        return ExplicitEmptyDictValue()

    if isinstance(result, list) and result == []:
        return ExplicitEmptyListValue()

    return result


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


class ExplicitEmptyListValue:
    """
    A special type used to explicitly pass empty lists to the API.
    """


class ExplicitEmptyDictValue:
    """
    A special type used to explicitly pass empty dictionaries to the API.
    """


def wrap_parse_nullable_value(arg_type: str) -> TYPES:
    """
    A helper function to parse `null` as None for nullable CLI args.
    This is intended to be called and passed to the `type=` kwarg for ArgumentParser.add_argument.

    :param arg_type: The arg type.
    :type arg_type: str

    :returns: The nullable value of the type.
    :rtype: TYPES
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

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: List,
        option_string: str = None,
    ):
        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, [])

        output_list = getattr(namespace, self.dest)

        # If a user has already specified an [] but is specifying
        # another value, assume "[]" was intended to be a literal.
        if isinstance(output_list, ExplicitEmptyListValue):
            setattr(namespace, self.dest, ["[]", values])
            return

        # If the output list is empty and the user specifies a []
        # argument, set the list to an explicitly empty list.
        if values == "[]" and len(output_list) < 1:
            setattr(namespace, self.dest, ExplicitEmptyListValue())
            return

        output_list.append(values)


class ListArgumentAction(argparse.Action):
    """
    This action is intended to be used only with list arguments.
    Its purpose is to aggregate adjacent object fields and produce consistent
    lists in the output namespace.
    """

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: List,
        option_string: str = None,
    ):
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

        # Find the deepest field, so we can know if
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

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str,
        option_string: str = None,
    ):
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

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str,
        option_string: str = None,
    ):
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

    def __init__(self, parameter: openapi3.paths.Parameter):
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

    def __init__(
        self, command, operation: Operation, method, params
    ):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """
        Wraps an openapi3.Operation object and handles pulling out values relevant
        to the Linode CLI.
         note::
           This function runs _before pickling!  As such, this is the only place
           where the OpenAPI3 objects can be accessed safely (as they are not
           usable when unpickled!)
        """
        self.request = None
        self.responses = {}
        self.response_model = None
        self.allowed_defaults = None

        # The legacy spec uses "200" (str) in response keys
        # while the new spec uses 200 (int).
        response_key = "200" if "200" in operation.responses else 200

        if (
            response_key in operation.responses
            and "application/json" in operation.responses[response_key].content
        ):
            self.response_model = OpenAPIResponse(
                operation.responses[response_key].content["application/json"]
            )

        if method in ("post", "put") and operation.requestBody:
            content = operation.requestBody.content

            if (
                "application/json" in content
                and content["application/json"].schema is not None
            ):
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

        # Ensure the summary has punctuation
        self.summary = operation.summary.rstrip(".") + "."

        self.description_rich, self.description = simplify_description(
            operation.description or ""
        )

        # The apiVersion attribute should not be specified as a positional argument
        self.params = [
            OpenAPIOperationParameter(param)
            for param in params
            if param.name not in {"apiVersion"}
        ]

        # Validation to ensure no conflicting arguments & param names are found.
        # This is necessary because arguments and parameters are both parsed into the
        # same result namespace by argparse.
        if self.request is not None and hasattr(self.request, "attrs"):
            param_names = {param.name for param in self.params}

            for attr in self.request.attrs:
                if attr not in param_names:
                    continue

                raise ValueError(
                    f"Attribute {attr.name} conflicts with parameter of the same name"
                )

        (
            self.url_base,
            self.url_path,
            self.default_api_version,
        ) = self._get_api_url_components(operation, params)

        self.url = self.url_base + self.url_path

        self.docs_url = self._resolve_operation_docs_url(operation)

        if self.docs_url is None:
            logging.warning(
                "%s %s Could not resolve docs URL for operation",
                self.method.upper(),
                self.url_path,
            )

        code_samples_ext = operation.extensions.get("code-samples")
        self.samples = (
            [v for v in code_samples_ext if v.get("lang").lower() == "cli"]
            if code_samples_ext is not None
            else []
        )

    @property
    def args(self):
        """
        Return a list of attributes from the request schema
        """
        return self.request.attrs if self.request else []

    @property
    def arg_routes(self) -> Dict[str, List[OpenAPIRequestArg]]:
        """
        Return a list of attributes from the request schema
        """
        return self.request.attr_routes if self.request else []

    @property
    def attrs(self):
        """
        Return a list of attributes from the request schema
        """
        return self.response_model.attrs if self.response_model else []

    @staticmethod
    def _flatten_url_path(tag: str) -> str:
        """
        Returns the lowercase of the tag to build up url path. Replace space with hyphen.

        :param tag: The tag value to be flattened.
        :type tag: str

        :returns: The flattened tag.
        :rtype: str
        """

        new_tag = tag.lower()
        new_tag = re.sub(r"[^a-z ]", "", new_tag).replace(" ", "-")
        return new_tag

    @staticmethod
    def _resolve_api_version(
        params: List[Parameter], server_url: str
    ) -> Optional[str]:
        """
        Returns the API version for a given list of params and target URL.

        :param params: The params for this operation's endpoint path.
        :type params: List[Parameter]
        :param server_url: The URL of server for this operation.
        :type server_url: str

        :returns: The default API version if the URL has a version, else None.
        :rtype: Optional[str]
        """

        # Remove empty segments from the URL path, stripping the first,
        # last and any duplicate slashes if necessary.
        # There shouldn't be a case where this is needed, but it's
        # always good to make things more resilient :)
        url_path_segments = [
            seg for seg in urlparse(server_url).path.split("/") if len(seg) > 0
        ]
        if len(url_path_segments) > 0:
            return "/".join(url_path_segments)

        version_param = next(
            (
                param
                for param in params
                if param.name == "apiVersion" and param.in_ == "path"
            ),
            None,
        )
        if version_param is not None:
            schema = version_param.schema

            if schema.default:
                return schema.default

            if schema.enum and len(schema.enum) > 0:
                return schema.enum[0]

        return None

    @staticmethod
    def _get_api_url_components(
        operation: Operation, params: List[Parameter]
    ) -> Tuple[str, str, str]:
        """
        Returns the URL components for a given operation.

        :param operation: The operation to get the URL components for.
        :type operation: Operation
        :param params: The parameters for this operation's route.
        :type params: List[Parameter]

        :returns: The base URL, path, and default API version of the operation.
        :rtype: Tuple[str, str, str]
        """

        url_server = (
            operation.servers[0].url
            if operation.servers
            # pylint: disable-next=protected-access
            else operation._root.servers[0].url
        )

        url_base = urlparse(url_server)._replace(path="").geturl()
        url_path = operation.path[-2]

        api_version = OpenAPIOperation._resolve_api_version(params, url_server)
        if api_version is None:
            raise ValueError(
                f"Failed to resolve API version for operation {operation}"
            )

        # The apiVersion is only specified in the new-style OpenAPI spec,
        # so we need to manually insert it into the path to maintain
        # backwards compatibility
        if "{apiVersion}" not in url_path:
            url_path = "/{apiVersion}" + url_path

        return url_base, url_path, api_version

    def process_response_json(
        self, json: Dict[str, Any], handler: OutputHandler
    ):  # pylint: disable=redefined-outer-name
        """
        Processes the response as JSON and prints.

        :param json: The json response.
        :type json: Dict[str, Any]

        :param handler: The CLI output handler.
        :type handler: OutputHandler
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

    def _add_args_filter(self, parser: argparse.ArgumentParser):
        """
        Builds up filter args for GET operation.

        :param parser: The parser to use.
        :type parser: ArgumentParser
        """

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

    def _add_args_post_put(
        self, parser: argparse.ArgumentParser
    ) -> List[Tuple[str, str]]:
        """
        Builds up args for POST and PUT operations.

        :param parser: The parser to use.
        :type parser: ArgumentParser

        :returns: A list of arguments.
        :rtype: List[Tuple[str, str]]
        """

        list_items = []

        # build args for body JSON
        for arg in self.args:
            if arg.read_only:
                continue

            arg_name_unescaped = unescape_arg_segment(arg.name)
            arg_path_unescaped = unescape_arg_segment(arg.path)

            arg_type = (
                arg.item_type if arg.datatype == "array" else arg.datatype
            )
            arg_type_handler = TYPES[arg_type]

            if arg.nullable:
                arg_type_handler = wrap_parse_nullable_value(arg_type)

            if arg.datatype == "array":
                # special handling for input arrays
                parser.add_argument(
                    "--" + arg_path_unescaped,
                    dest=arg.path,
                    metavar=arg_name_unescaped,
                    action=ArrayAction,
                    type=arg_type_handler,
                )
            elif arg.is_child:
                parser.add_argument(
                    "--" + arg_path_unescaped,
                    dest=arg.path,
                    metavar=arg_name_unescaped,
                    action=ListArgumentAction,
                    type=arg_type_handler,
                )
                list_items.append((arg.path, arg.parent))
            else:
                if arg.datatype == "string" and arg.format == "password":
                    # special case - password input
                    parser.add_argument(
                        "--" + arg_path_unescaped,
                        nargs="?",
                        action=PasswordPromptAction,
                    )
                elif arg.datatype == "string" and arg.format in (
                    "file",
                    "ssl-cert",
                    "ssl-key",
                ):
                    parser.add_argument(
                        "--" + arg_path_unescaped,
                        dest=arg.path,
                        metavar=arg_name_unescaped,
                        action=OptionalFromFileAction,
                        type=arg_type_handler,
                    )
                else:
                    parser.add_argument(
                        "--" + arg_path_unescaped,
                        dest=arg.path,
                        metavar=arg_name_unescaped,
                        type=arg_type_handler,
                    )

        return list_items

    def _validate_parent_child_conflicts(self, parsed: argparse.Namespace):
        """
        This method validates that no child arguments (e.g. --interfaces.purpose) are
        specified alongside their parent (e.g. --interfaces).

        :param parsed: The parsed arguments.
        :type parsed: Namespace
        """
        conflicts = defaultdict(list)

        for arg in self.args:
            parent = arg.parent
            arg_value = getattr(parsed, arg.path, None)

            if parent is None or arg_value is None:
                continue

            # Special case to ignore child arguments that are not specified
            # but are implicitly populated by ListArgumentAction.
            if isinstance(arg_value, list) and arg_value.count(None) == len(
                arg_value
            ):
                continue

            # If the parent isn't defined, we can
            # skip this one
            if getattr(parsed, parent) is None:
                continue

            # We found a conflict
            conflicts[parent].append(arg)

        # No conflicts found
        if len(conflicts) < 1:
            return

        for parent, args in conflicts.items():
            arg_format = ", ".join([f"--{v.path}" for v in args])
            print(
                f"Argument(s) {arg_format} cannot be specified when --{parent} is specified.",
                file=sys.stderr,
            )

        sys.exit(ExitCodes.ARGUMENT_ERROR)

    @staticmethod
    def _handle_list_items(
        list_items: List[Tuple[str, str]], parsed: argparse.Namespace
    ) -> (
        argparse.Namespace
    ):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """
        Groups list items and parses nested list.

        :param list_items: The list items to be handled.
        :type list_items: List[Tuple[str, str]]

        :param parsed: The parsed arguments.
        :type parsed: argparse.Namespace

        :returns: The parsed arguments updated with the list items.
        :rtype: argparse.Namespace
        """

        lists = {}

        # group list items as expected
        for arg_name, list_name in list_items:
            item_name = arg_name.split(list_name)[1][1:]

            if hasattr(parsed, arg_name):
                val = getattr(parsed, arg_name) or []
                if not val:
                    continue

                if list_name not in lists:
                    lists[list_name] = []

                target_list = lists[list_name]

                # If there are any additional indices not accounted for
                # in the target list, add new objects accordingly.
                if len(target_list) < len(val):
                    for _ in range(len(val) - len(target_list)):
                        target_list.append({})

                # Populate each entry in the target list
                # with each corresponding entry in val.
                for obj, item in zip(target_list, val):
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

    def parse_args(self, args: Any) -> argparse.Namespace:
        """
        Given sys.argv after the operation name, parse args based on the params
        and args of this operation

        :param args: The arguments to be parsed.
        :type args: Any

        :returns: The parsed arguments.
        :rtype: Namespace
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

        parsed = parser.parse_args(args)

        if self.method in ("post", "put"):
            self._validate_parent_child_conflicts(parsed)

        return self._handle_list_items(list_items, parsed)

    @staticmethod
    def _resolve_operation_docs_url_legacy(
        operation: Operation,
    ) -> Optional[str]:
        """
        Gets the docs URL for a given operation in the legacy OpenAPI spec.

        :param operation: The target openapi3.Operation to get the docs URL for.
        :type operation: str

        :returns: The docs URL if it can be resolved, else None
        :rtype: Optional[str]
        """
        tags = operation.tags
        if tags is None or len(tags) < 1 or len(operation.summary) < 1:
            return None

        tag_path = OpenAPIOperation._flatten_url_path(tags[0])
        summary_path = OpenAPIOperation._flatten_url_path(operation.summary)
        return f"https://www.linode.com/docs/api/{tag_path}/#{summary_path}"

    @staticmethod
    def _resolve_operation_docs_url(operation: Operation) -> Optional[str]:
        """
        Gets the docs URL for a given OpenAPI operation.

        :param operation: The target openapi3.Operation to get the docs URL for.
        :type operation: str

        :returns: The docs URL if it can be resolved, else None
        :rtype: Optional[str]
        """
        # Case for TechDocs
        if (
            operation.externalDocs is not None
            and operation.externalDocs.url is not None
        ):
            return operation.externalDocs.url

        # Case for legacy docs
        return OpenAPIOperation._resolve_operation_docs_url_legacy(operation)
