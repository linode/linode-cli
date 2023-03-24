"""
Responsible for managing spec and routing commands to operations.
"""

import os
import pickle
import re
import sys
from sys import version_info
from openapi3 import OpenAPI

from .api_request import do_request
from .configuration import CLIConfig
from .helpers import filter_markdown_links
from .operation import CLIArg, CLIOperation, URLParam
from .output import OutputHandler, OutputMode
from .response import ModelAttr, ResponseModel

METHODS = ("get", "post", "put", "delete")


class CLI:  # pylint: disable=too-many-instance-attributes
    """
    Responsible for loading or baking a spec and handling incoming commands
    """

    def __init__(self, version, base_url, skip_config=False):
        self.ops = {}
        self.spec = {}
        self.defaults = True  # whether to use default values for arguments
        self.page = 1
        self.page_size = 100
        self.debug_request = False
        self.version = version
        self.base_url = base_url
        self.spec_version = "None"
        self.suppress_warnings = False

        self.output_handler = OutputHandler()
        self.config = CLIConfig(self.base_url, skip_config=skip_config)
        self.load_baked()

    def _parse_properties(self, node, prefix=None):
        """
        Given the value of a "properties" node, parses out the attributes and
        returns them as a list
        """
        if prefix is None:
            prefix = []
        attrs = []
        for name, info in node.items():
            if "properties" in info:
                attrs += self._parse_properties(
                    info["properties"], prefix + [name]
                )
            else:
                item_type = None
                item_container = info.get("items")
                if item_container:
                    item_type = item_container.get("type")
                attrs.append(
                    ModelAttr(
                        ".".join(prefix + [name]),
                        info.get("x-linode-filterable") or False,
                        info.get("x-linode-cli-display") or False,
                        info.get("type") or "string",
                        color_map=info.get("x-linode-cli-color"),
                        item_type=item_type,
                    )
                )

        return attrs

    def bake(
        self, spec
    ):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """
        Generates ops and bakes them to a pickle
        """
        spec = OpenAPI(spec)
        self.spec = spec
        self.ops = {}
        default_servers = [c.url for c in spec.servers]
        ext = {
            'skip': 'linode-cli-skip',
            'action': 'linode-cli-action',
            'command': 'linode-cli-command',
            'defaults': 'linode-cli-allowed-defaults',
        }

        for path in spec.paths:
            if hasattr(spec.paths[path], 'extensions'):
                if ext['command'] in spec.paths[path].extensions:
                    command = spec.paths[path].extensions[ext['command']]
                else:
                    continue

            for method in METHODS:
                if (hasattr(spec.paths[path], method)
                    and hasattr(getattr(spec.paths[path], method), 'extensions')):
                    method_spec = getattr(spec.paths[path], method)
                    extensions = method_spec.extensions
                    if ext['skip'] in extensions:
                        continue
                    if ext['action'] in extensions:
                        action = extensions[ext['action']]
                        if isinstance(action, list):
                            action_alias = action[1:]
                            action = action[0]
                        self.ops[command][action] = {}
                    else:
                        continue
                else:
                    continue

                request_schema = method_spec.requestBody.content['application/json'].schema
                response_schema = method_spec.respones['200'].content['application/json'].schema

                summary = method_spec.summary
                required_fields = request_schema.required
                allowed_defaults = method_spec.extensions[ext['defaults']] or None

                args = {}
                params = {}
                response_model={}

                docs_url = None
                tags = method_spec.tags
                if tags is not None and len(tags) > 0 and len(summary) > 0:
                    tag_path = self._flatten_url_path(tags[0])
                    summary_path = self._flatten_url_path(summary)
                    docs_url = f"https://www.linode.com/docs/api/{tag_path}/#{summary_path}"

                use_servers = (
                    [c.url for c in spec.servers]
                    if hasattr(method_spec, 'servers')
                    else default_servers
                )

                cli_args = []
                for arg, info in args.items():
                    new_arg = CLIArg(
                        info["name"],
                        info["type"],
                        filter_markdown_links(
                            info["desc"].split(".")[0] + "."
                        ),
                        arg,
                        info["format"],
                        list_item=info.get("list_item"),
                    )

                    if arg in required_fields:
                        new_arg.required = True

                    # handle arrays
                    if "item_type" in info:
                        new_arg.arg_item_type = info["item_type"]
                    cli_args.append(new_arg)

                # looks for param names that will be obscured by args
                # clone the params since they're shared by all methods in this
                # path, and we only want to modify this method's params
                use_params = [c.clone() for c in params]
                use_path = path
                for p in use_params:
                    if p.name in args:
                        # or (m == 'get' and p.name in model_attrs):
                        # if we found a parameter name that is also and argument name
                        # append an underscore to both the parameter name and the
                        # parameter name in the URL
                        use_path = use_path.replace(
                            "{" + p.name + "}", "{" + p.name + "_}"
                        )
                        p.name += "_"

                self.ops[command][action] = CLIOperation(
                    command,
                    action,
                    method,
                    use_path,
                    summary,
                    cli_args,
                    response_model,
                    use_params,
                    use_servers,
                    docs_url=docs_url,
                    allowed_defaults=allowed_defaults,
                    action_aliases=action_alias,
                )

        # hide the base_url from the spec away
        self.ops["_base_url"] = spec["servers"][0]["url"]
        self.ops["_spec_version"] = spec["info"]["version"]

        # finish the baking
        data_file = self._get_data_file()
        with open(data_file, "wb") as f:
            pickle.dump(self.ops, f)

    def load_baked(self):
        """
        Loads a baked spec representation from a baked pickle
        """
        data_file = self._get_data_file()
        data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), data_file
        )
        if os.path.exists(data_path):
            with open(data_path, "rb") as f:
                self.ops = pickle.load(f)
                if "_base_url" in self.ops:
                    self.base_url = self.ops["_base_url"]
                    del self.ops["_base_url"]
                if "_spec_version" in self.ops:
                    self.spec_version = self.ops["_spec_version"]
                    del self.ops["_spec_version"]
        else:
            print(
                "No spec baked.  Please bake by calling this script as follows:"
            )
            print("  python3 gen_cli.py bake /path/to/spec")
            self.ops = None  # this signals __init__.py to give up

    def _get_data_file(self):
        """
        Returns the name of the baked data file this program wants.  This is in
        part based on python version.
        """
        return f"data-{version_info[0]}"

    @staticmethod
    def _flatten_url_path(tag):
        new_tag = tag.lower()
        new_tag = re.sub(r"[^a-z ]", "", new_tag).replace(" ", "-")
        return new_tag

    def handle_command(self, command, action, args):
        """
        Given a command, action, and remaining kwargs, finds and executes the
        action
        """
        if (command, action) in [
            ("linodes", "ips-list"),
            ("firewalls", "rules-list"),
        ] and "--json" not in args:
            print(
                "This output contains a nested structure that may not properly "
                + "be displayed by linode-cli.",
                "A fix is currently on the roadmap but has not yet been implemented.",
                "Please use --json for endpoints like this in the meantime.",
                file=sys.stderr,
            )

        try:
            operation = self.find_operation(command, action)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

        result = do_request(self, operation, args)

        operation.process_response_json(result.json(), self.output_handler)

        if (
            self.output_handler.mode == OutputMode.table
            and "pages" in result.json()
            and result.json()["pages"] > 1
        ):
            print(
                f"Page {result.json()['page']} of {result.json()['pages']}. "
                "Call with --page [PAGE] to load a different page."
            )

    def configure(self):
        """
        Reconfigure the application
        """
        self.config.configure()

    def call_operation(self, command, action, args=None, filters=None):
        """
        This function is used in plugins to retrieve the result of CLI operations
        in JSON format.  This uses the configured user of the CLI.

        :param filters: The X-Filter header to include in the request.  This overrides
                        whatever is passed into to command as filters.
        :type filters: dict
        """
        if args is None:
            args = []
        if command not in self.ops or action not in self.ops[command]:
            raise ValueError(f"Unknown command/action {command}/{action}")

        operation = self.ops[command][action]

        result = do_request(
            self,
            operation,
            args,
            filter_header=filters,
            skip_error_handling=True,
        )

        return result.status_code, result.json()

    def find_operation(self, command, action):
        """
        Finds the corresponding operation for the given command and action.
        """
        if command not in self.ops:
            raise ValueError(f"Command not found: {command}")

        command_dict = self.ops[command]

        if action in command_dict:
            return command_dict[action]

        # Find the matching alias
        for op in command_dict.values():
            if action in op.action_aliases:
                return op

        # Fail if no matching alias was found
        raise ValueError(f"No action {action} for command {command}")
