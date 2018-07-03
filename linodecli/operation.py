"""
Classes related to OpenAPI-defined operations and their arguments and parameters.
"""
from __future__ import print_function

import argparse
from getpass import getpass
import json
from os import path


def parse_boolean(value):
    """
    A helper to allow accepting booleans in from argparse.  This is intended to
    be passed to the `type=` kwarg for ArgumentParser.add_argument.
    """
    if value.lower() in ('yes', 'true', 'y', '1'):
        return True
    if value.lower() in ('no', 'false', 'n', '0'):
        return False
    raise argparse.ArgumentTypeError('Expected a boolean value')


def parse_dict(value):
    """
    A helper function to decode incoming JSON data as python dicts.  This is
    intended to be passed to the `type=` kwarg for ArgumentParaser.add_argument.
    """
    if not isinstance(value, str):
        print("not a string :(")
        raise argparse.ArgumentTypeError('Expected a JSON string')
    try:
        return json.loads(value)
    except:
        raise argparse.ArgumentTypeError('Expected a JSON string')


class PasswordPromptAction(argparse.Action):
    """
    A special argparse Action to handle prompting for password.  Also accepts
    passwords on the terminal to allow for backwards-compatible behavior.
    """
    def __init__(self, *args, **kwargs):
        super(PasswordPromptAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if values:
            if isinstance(values, str):
                password = values
            else:
                raise argparse.ArgumentTypeError('Expected a string (or leave blank for prompt)')
        else:
            prompt = 'Value for {}: '.format(self.dest)
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
            raise argparse.ArgumentTypeError('Expected a string')


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
    def __init__(self, name, arg_type, description, path, arg_format):
        self.name = name
        self.arg_type = arg_type
        self.arg_format = arg_format
        self.description = description.replace('\n', '').replace('\r', '')
        self.path = path
        self.arg_item_type = None # populated during baking for arrays
        self.required = False # this is set during baking


class URLParam:
    """
    An argument passed to the CLI positionally. These are defined in a path in
    the OpenAPI spec, in a "parameters" block
    """
    def __init__(self, name, param_type):
        self.name = name
        self.param_type = param_type


class CLIOperation:
    """
    A single operation described by the OpenAPI spec.  An operation is a method
    on a path, and should have a unique operationId to identify it.  Operations
    are responsible for parsing their own arguments and processing their
    responses with the help of their ResponseModel
    """
    def __init__(self, method, url, summary, args, response_model,
                 params):
        self.method = method
        self.url = url
        self.summary = summary
        self.args = args
        self.response_model = response_model
        self.params = params

    def parse_args(self, args):
        """
        Given sys.argv after the operation name, parse args based on the params
        and args of this operation
        """
        #  build an argparse
        parser = argparse.ArgumentParser(description=self.summary)
        for param in self.params:
            parser.add_argument(param.name, metavar=param.name,
                                type=TYPES[param.param_type])

        if self.method == "get":
            # build args for filtering
            for attr in self.response_model.attrs:
                if attr.filterable:
                    parser.add_argument('--'+attr.name, metavar=attr.name)

        elif self.method in ("post", "put"):
            # build args for body JSON
            for arg in self.args:
                if arg.arg_type == 'array':
                    # special handling for input arrays
                    parser.add_argument('--'+arg.path, metavar=arg.name,
                                        action='append', type=TYPES[arg.arg_item_type])
                else:
                    if arg.arg_type == 'string' and arg.arg_format == 'password':
                        # special case - password input
                        parser.add_argument('--'+arg.path, nargs='?', action=PasswordPromptAction)
                    elif arg.arg_type == 'string' and arg.arg_format in ('ssl-cert','ssl-key'):
                        parser.add_argument('--'+arg.path, metavar=arg.name,
                                            action=OptionalFromFileAction,
                                            type=TYPES[arg.arg_type])
                    else:
                        parser.add_argument('--'+arg.path, metavar=arg.name,
                                            type=TYPES[arg.arg_type])

        parsed = parser.parse_args(args)
        return parsed

    def process_response_json(self, json, handler):
        if self.response_model is None:
            return

        if 'pages' in json:
            json = json['data']
        else:
            json = [json]

        handler.print(self.response_model, json)
