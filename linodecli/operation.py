"""
Classes related to OpenAPI-defined operations and their arguments and parameters.
"""

import argparse
import json
from getpass import getpass
from os import environ, path


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
    except:
        raise argparse.ArgumentTypeError("Expected a JSON string")


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
        environ_key = "LINODE_CLI_{}".format(self.dest.upper())

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
            prompt = "Value for {}: ".format(self.dest)
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
            if path.exists(input_path) and path.isfile(input_path):
                with open(input_path) as f:
                    data = f.read()
                setattr(namespace, self.dest, data)
            else:
                setattr(namespace, self.dest, values)
        else:
            raise argparse.ArgumentTypeError("Expected a string")


TYPES = {
    "string": str,
    "integer": int,
    "boolean": parse_boolean,
    "array": list,
    "object": parse_dict,
    "number": float,
}


class CLIArg:
    """
    An argument passed to the CLI with a flag, such as `--example value`.  These
    are defined in a requestBody in the api spec.
    """

    def __init__(self, name, arg_type, description, path, arg_format, list_item=None):
        self.name = name
        self.arg_type = arg_type
        self.arg_format = arg_format
        self.description = description.replace("\n", "").replace("\r", "")
        self.path = path
        self.arg_item_type = None  # populated during baking for arrays
        self.required = False  # this is set during baking
        self.list_item = list_item


class URLParam:
    """
    An argument passed to the CLI positionally. These are defined in a path in
    the OpenAPI spec, in a "parameters" block
    """

    def __init__(self, name, param_type):
        self.name = name
        self.param_type = param_type

    def clone(self):
        """
        Returns a new URLParam that is exactly like this one
        """
        return URLParam(self.name, self.param_type)


class CLIOperation:
    """
    A single operation described by the OpenAPI spec.  An operation is a method
    on a path, and should have a unique operationId to identify it.  Operations
    are responsible for parsing their own arguments and processing their
    responses with the help of their ResponseModel
    """

    def __init__(
        self,
        command,
        action,
        method,
        url,
        summary,
        args,
        response_model,
        params,
        servers,
        docs_url=None,
        allowed_defaults=None,
        action_aliases=None,
    ):
        self.command = command
        self.action = action
        self.method = method
        self._url = url
        self.summary = summary
        self.args = args
        self.response_model = response_model
        self.params = params
        self.servers = servers
        self.docs_url = docs_url
        self.allowed_defaults = allowed_defaults
        self.action_aliases = action_aliases or []

    @property
    def url(self):
        """
        Returns the full URL for this resource based on servers and endpoint
        """
        base_url = self.servers[0]
        return base_url + "/" + self._url

    def parse_args(self, args):
        """
        Given sys.argv after the operation name, parse args based on the params
        and args of this operation
        """
        list_items = []

        #  build an argparse
        parser = argparse.ArgumentParser(
            prog="linode-cli {} {}".format(self.command, self.action),
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
                            "--" + attr.name, type=expected_type, metavar=attr.name
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
                    if arg.arg_type == "string" and arg.arg_format == "password":
                        # special case - password input
                        parser.add_argument(
                            "--" + arg.path, nargs="?", action=PasswordPromptAction
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
                            "--" + arg.path, metavar=arg.name, type=TYPES[arg.arg_type]
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

    def process_response_json(self, json, handler):
        if self.response_model is None:
            return

        json = self.response_model.fix_json(json)

        handler.print(self.response_model, json)
