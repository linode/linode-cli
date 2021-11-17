import argparse


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
        # if not provided on the command line, pull from the environment if it
        # exists at this key
        environ_key = "LINODE_CLI_{}".format(self.dest.upper())

        if values:
            if isinstance(values, str):
                password = values
            else:
                raise argparse.ArgumentTypeError('Expected a string (or leave blank for prompt)')
        elif environ_key in environ:
            password = environ.get(environ_key)
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


#: TYPES is a mapping of OpenAPI type strings into python types
TYPES = {
    "string": str,
    "integer": int,
    "boolean": parse_boolean,
    "array": list,
    "object": parse_dict,
    "number": float,
}


def parse_args(operation, args):
    """
    Given an operation and the sys.argv after the operation name, parse args
    based on the params and args of the operation.
    
    :param operation: The operation we're parsing args for
    :type operation: linodecli.baked.OpenAPIOperation
    :param args: The args we're parsing; this is sys.argv after the command and action
                 have been removed (which is necessary to find the operation).
    :type args: list[str]
    """
    list_items = []

    #  build an argparse
    parser = argparse.ArgumentParser(description=operation.summary)
    for param in operation.params:
        parser.add_argument(param.name, metavar=param.name,
                            type=TYPES[param.param_type])

    if operation.method == "get":
        # build args for filtering
        for attr in operation.response_model.attrs:
            if attr.filterable:
                expected_type = TYPES[attr.datatype]
                if expected_type == list:
                    parser.add_argument('--'+attr.name, type=TYPES[attr.item_type],
                                        metavar=attr.name, nargs='?')
                else:
                    parser.add_argument('--'+attr.name, type=expected_type, metavar=attr.name)

    elif operation.method in ("post", "put"):
        # build args for body JSON
        for arg in operation.args:
            if arg.arg_type == 'array':
                # special handling for input arrays
                parser.add_argument('--'+arg.path, metavar=arg.name,
                                    action='append', type=TYPES[arg.arg_item_type])
            elif arg.list_item is not None:
                parser.add_argument('--'+arg.path, metavar=arg.name,
                                    action='append', type=TYPES[arg.arg_type])
                list_items.append((arg.path, arg.list_item))
            else:
                if arg.arg_type == 'string' and arg.arg_format == 'password':
                    # special case - password input
                    parser.add_argument('--'+arg.path, nargs='?', action=PasswordPromptAction)
                elif arg.arg_type == 'string' and arg.arg_format in ('file','ssl-cert','ssl-key'):
                    parser.add_argument('--'+arg.path, metavar=arg.name,
                                        action=OptionalFromFileAction,
                                        type=TYPES[arg.arg_type])
                else:
                    parser.add_argument('--'+arg.path, metavar=arg.name,
                                        type=TYPES[arg.arg_type])

    parsed = parser.parse_args(args)

    lists = {}
    # group list items as expected
    for arg_name, list_name in list_items:
        item_name = arg_name.split('.')[-1]
        if hasattr(parsed, arg_name):
            val = getattr(parsed, arg_name) or []
            if  list_name not in lists:
                new_list = [{item_name: c} for c in val]
                lists[list_name] = new_list
            else:
                update_list = lists[list_name]
                for obj, item in zip(update_list, val):
                    obj[item_name] = item

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
